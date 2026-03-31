import requests
import json
import re
from typing import Optional
from jinja2 import Template, Environment, FileSystemLoader
from PIL import Image
import sys
from pathlib import Path
import base64
from datetime import datetime
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from python_rewrite.setting import get_settings

settings = get_settings()
effective_key = ("" or settings.openai_api_key).strip()
effective_model = ("" or settings.openai_model).strip()
raw_base_url = (settings.openai_base_url or "").strip()

effective_base_url = f"{raw_base_url.rstrip('/')}/{effective_model}:generateContent"

"""构造符合本项目签名的 ai_call 函数。"""
def _ai_call(system: str, user: str, images: Optional[list[dict]] = None) -> str:
    # 有视觉输入时，按 OpenAI 多模态消息格式传递
    user_content: list[dict] = [{"text": user}]
    print("user_content:\n",user_content)
    if images:  
        for idx, img in enumerate(images):
            src = str(img.get("src", "")).strip()
            if not src:
                continue
            # 提取图片名称
            img_name = Path(src).name
            # 提取图片类型
            img_type = Path(src).suffix[1:].lower()
            # 读取图片
            with open(src, "rb") as f:
                image_bytes = f.read()
            user_content.append({
                "text":f"图片名称：{img_name}，图片编号：image_{idx}"
            })
            user_content.append({
                "inlineData": {
                    "mimeType": f"image/{img_type}",
                    "data":base64.b64encode(image_bytes).decode("utf-8")
                }
            })
        messages: list[dict] = [
            {"role": "user", "parts": user_content},
        ]
    else:
        messages = [
            {"role": "user", "parts": user_content}
        ]
    
    payload = {
        "systemInstruction": {
            "role":"system",
            "parts":[{"text": system}]
        },
        "contents": messages,
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"]  # 同时返回文字 + 图片
        }
    }
    headers = {
        "x-goog-api-key": effective_key,
        "Content-Type": "application/json",
    }

    resp = requests.post(effective_base_url, headers=headers, json=payload)
    print("HTTP STATUS:", resp.status_code)
    # print("RESPONSE BODY:", resp.text)
    resp.raise_for_status()

    try:
        data = resp.json()
        content = json.dumps(data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        content = resp.text

    return content or ""

# 读取md文档
def read_md_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 获取prompt模板
def get_template(file_path:str, prompt_name:str) -> Template:
    env = Environment(loader=FileSystemLoader(file_path))
    tpl = env.get_template(prompt_name)
    return tpl

# 获取图像images
def get_images(images_path: str, num: int) -> dict:
    images_list:list[dict] = []

    for _ in range(num):
        # 获取尺寸等信息可以根据需要添加
        with Image.open(images_path) as img:
            width, height = img.size
        
        # 提取图片名称
        img_name = Path(images_path).name

        images_list.append({"name": f"{img_name}", "src": images_path, "width": width, "height": height})
    
    return images_list

def _extract_json_payload(text: str):
    """从文本中提取 JSON，兼容 ```json 代码块 和 前后说明文字。"""
    s = (text or "").strip()
    if not s:
        raise ValueError("模型返回的文本为空，无法解析 JSON。")

    decoder = json.JSONDecoder()

    def _try_raw_decode(candidate: str):
        c = candidate.strip()
        if not c:
            return None
        try:
            obj, _ = decoder.raw_decode(c)
            return obj
        except json.JSONDecodeError:
            return None

    if "```" in s:
        chunks = s.split("```")
        for chunk in chunks:
            candidate = chunk.strip()
            if not candidate:
                continue
            # 兼容 ```json / ```JSON / ```json5 等标记
            candidate = re.sub(r"^(json\w*)\s*", "", candidate, flags=re.IGNORECASE)
            obj = _try_raw_decode(candidate)
            if obj is not None:
                return obj

    # 兜底：在整段文本中扫描第一个可解析的 JSON 起点
    for i, ch in enumerate(s):
        if ch not in "[{":
            continue
        obj = _try_raw_decode(s[i:])
        if obj is not None:
            return obj

    preview = s[:200].replace("\n", "\\n")
    raise ValueError(f"未找到可解析的 JSON。文本前缀: {preview}")


def _is_scene_list(value) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if not all(isinstance(item, dict) for item in value):
        return False
    required_keys = {"title", "description", "type"}
    return all(required_keys.issubset(item.keys()) for item in value)


def _normalize_scenes_payload(value) -> list:
    """兼容 list[scene] 与 {"scenes": [...]} 两种结构。"""
    if _is_scene_list(value):
        return value
    if isinstance(value, dict):
        scenes = value.get("scenes")
        if _is_scene_list(scenes):
            return scenes
    return []


def _extract_scenes_from_texts(texts: list[str]) -> list:
    # 优先解析拼接后的完整文本，兼容被切碎的 JSON 输出
    full_text = "".join(texts).strip()
    if full_text:
        try:
            candidate = _extract_json_payload(full_text)
            scenes = _normalize_scenes_payload(candidate)
            if scenes:
                return scenes
        except ValueError:
            pass

    # 回退：逐段尝试
    for text in texts:
        try:
            candidate = _extract_json_payload(text)
        except ValueError:
            continue
        scenes = _normalize_scenes_payload(candidate)
        if scenes:
            return scenes
    return []


def _save_inline_images(parts: list[dict], output_dir: str = "./generated_images") -> list[str]:
    saved_paths: list[str] = []
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    image_idx = 0
    for part in parts:
        if not isinstance(part, dict):
            continue
        inline = part.get("inlineData")
        if not isinstance(inline, dict):
            continue
        data_b64 = inline.get("data")
        if not data_b64:
            continue
        mime = str(inline.get("mimeType", "image/png"))
        ext = mime.split("/")[-1].lower().split(";")[0]
        if ext == "jpeg":
            ext = "jpg"
        filename = f"image_{image_idx}.{ext or 'png'}"
        path = out / filename
        path.write_bytes(base64.b64decode(data_b64))
        saved_paths.append(str(path))
        image_idx += 1
    return saved_paths


def _collect_urls_from_obj(value) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        for _, v in value.items():
            urls.extend(_collect_urls_from_obj(v))
    elif isinstance(value, list):
        for v in value:
            urls.extend(_collect_urls_from_obj(v))
    elif isinstance(value, str):
        s = value.strip()
        if s.startswith("http://") or s.startswith("https://"):
            urls.append(s)
    return urls


def _guess_ext_from_url(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ""


def _guess_ext_from_content_type(content_type: str) -> str:
    ct = (content_type or "").lower()
    if "image/png" in ct:
        return ".png"
    if "image/jpeg" in ct:
        return ".jpg"
    if "image/webp" in ct:
        return ".webp"
    if "image/gif" in ct:
        return ".gif"
    if "image/bmp" in ct:
        return ".bmp"
    return ""


def _save_images_from_text_urls(texts: list[str], output_dir: str = "./generated_images") -> list[str]:
    """从文本中提取图片 URL 并下载保存。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    full_text = "".join(texts).strip()
    url_candidates: list[str] = []

    # 先按 JSON 结构提取 URL
    if full_text:
        try:
            payload = _extract_json_payload(full_text)
            url_candidates.extend(_collect_urls_from_obj(payload))
        except ValueError:
            pass

    # 再用正则兜底提取 URL
    url_candidates.extend(re.findall(r"https?://[^\s\"'<>]+", full_text))

    # 去重且保持顺序
    seen: set[str] = set()
    urls: list[str] = []
    for u in url_candidates:
        cleaned = u.rstrip(".,;)")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            urls.append(cleaned)

    saved_paths: list[str] = []
    image_idx = 0
    for url in urls:
        try:
            resp = requests.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
        except requests.RequestException:
            continue

        ext = _guess_ext_from_content_type(resp.headers.get("Content-Type", ""))
        if not ext:
            ext = _guess_ext_from_url(str(resp.url))
        if not ext:
            # 非图片响应（例如网页短链），跳过
            continue

        path = out / f"image_from_url_{image_idx}{ext}"
        path.write_bytes(resp.content)
        saved_paths.append(str(path))
        image_idx += 1

    return saved_paths


def save_response_log(response_str: str, log_dir: Optional[str] = None) -> str:
    """保存 API 原始响应到日志文件，返回日志路径。"""
    base_dir = Path(log_dir) if log_dir else (Path(__file__).resolve().parent / "logs")
    base_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = base_dir / f"response_{ts}.json"
    log_path.write_text(response_str, encoding="utf-8")
    return str(log_path)


def extract_scenes(response_str: str) -> tuple[list, list[str]]:
    """从 API 原始响应中同时提取 scenes 与图片。"""
    data = json.loads(response_str)
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError(f"响应中不存在 candidates: {response_str[:500]}")

    all_parts: list[dict] = []
    for cand in candidates:
        parts = cand.get("content", {}).get("parts", [])
        if isinstance(parts, list):
            all_parts.extend(parts)

    text_parts: list[str] = []
    for p in all_parts:
        if not isinstance(p, dict):
            continue
        if p.get("thought") is True:
            continue
        txt = p.get("text")
        if isinstance(txt, str) and txt.strip():
            text_parts.append(txt)
    scenes = _extract_scenes_from_texts(text_parts)
    image_paths = _save_inline_images(all_parts)
    if not image_paths:
        image_paths = _save_images_from_text_urls(text_parts)
    return scenes, image_paths


TYPE_COLORS = {
    "slide":       ("#e8f4fd", "#1a73e8"),
    "interactive": ("#e8f8f0", "#1e8e3e"),
    "quiz":        ("#fef3e2", "#e37400"),
}

def save_html(scenes: list, output_path: str = "output.html"):
    rows = ""
    for scene in scenes:
        t = scene.get("type", "slide")
        bg, accent = TYPE_COLORS.get(t, ("#f5f5f5", "#555"))
        kp_html = "".join(f"<li>{kp}</li>" for kp in scene.get("keyPoints", []))
        duration = scene.get("estimatedDuration")
        duration_html = f'<span class="tag">⏱ {duration}s</span>' if duration else ""
        rows += f"""
        <div class="card" style="background:{bg};border-left:4px solid {accent}">
          <div class="card-header">
            <span class="badge" style="background:{accent}">{t}</span>
            <span class="order" style="color:{accent}">#{scene.get('order','')}</span>
            {duration_html}
          </div>
          <h2>{scene.get('title','')}</h2>
          <p class="desc">{scene.get('description','')}</p>
          <ul>{kp_html}</ul>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Scene 预览</title>
  <style>
    body {{ font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
            background:#f0f2f5; margin:0; padding:24px; }}
    h1   {{ text-align:center; color:#333; margin-bottom:24px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr));
             gap:20px; max-width:1200px; margin:0 auto; }}
    .card {{ border-radius:12px; padding:20px 24px; box-shadow:0 2px 8px rgba(0,0,0,.08); }}
    .card-header {{ display:flex; align-items:center; gap:8px; margin-bottom:10px; }}
    .badge {{ color:#fff; font-size:12px; padding:2px 10px;
              border-radius:20px; font-weight:600; }}
    .order {{ font-size:13px; font-weight:700; }}
    .tag   {{ font-size:12px; color:#666; margin-left:auto; }}
    h2     {{ margin:0 0 8px; font-size:17px; color:#111; }}
    .desc  {{ color:#555; font-size:14px; margin:0 0 12px; line-height:1.6; }}
    ul     {{ margin:0; padding-left:18px; color:#444; font-size:14px; }}
    li     {{ margin-bottom:4px; line-height:1.5; }}
  </style>
</head>
<body>
  <h1>Scene 预览（共 {len(scenes)} 个）</h1>
  <div class="grid">{rows}</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML 已保存至: {output_path}")


def run():

    # OpenMAIC的课件生成prompt

    # requirements = read_md_file("./docs-1774517356894/KLugdNuRIoGbSFxY8zXcf5A1njb.md")

    # system_tpl = get_template("./prompt/", "system_prompt.jinja")
    # user_tpl = get_template("./prompt/", "user_prompt.jinja")

    # images = [get_images("./docs-1774517356894/doc-parser-images-172916/847b2cac-cecd-49ba-8cfc-aea16ea78de6.jpg", 1)]

    # system_prompt = system_tpl.render()
    # user_prompt = user_tpl.render(
    #     requirements=requirements,
    #     language = "zh-CN",
    #     availableImages = images,
    #     userProfile = "高中学生"
    #     )


    # 课堂背景图生成prompt
    system_tpl = get_template("./prompt/", "system_gen_class_background.jinja")
    user_tpl = get_template("./prompt/", "user_gen_class_background.jinja")

    board_content = read_md_file("./class_materials/scene_02_board.md")
    character = read_md_file("./class_materials/scene_02_characters.md")
    base_ref_img = get_images("./class_materials/BASELINE_REFERENCE_IMAGE.png", 1)
    image_name = base_ref_img[0]["name"]

    system_prompt = system_tpl.render()
    user_prompt = user_tpl.render(
        IMAGE_BASE=image_name,
        CLASSROOM_CHARACTERS_DESCRIPTION = character,
        BOARD_CONTENT_DESCRIPTION = board_content
    )


    # # 课堂风格图生成prompt
    # system_tpl = get_template("./prompt/", "system_style_gen.jinja")
    # user_tpl = get_template("./prompt/", "user_style_gen.jinja")

    # system_prompt = system_tpl.render()
    # user_prompt = user_tpl.render()
    print(base_ref_img)
    response = _ai_call(system=system_prompt, user=user_prompt,images=base_ref_img)
    log_path = save_response_log(response)
    print(f"response log saved to: {log_path}")

    # 方式3：提取 JSON 并缩进打印
    scenes, image_paths = extract_scenes(response)
    print(json.dumps(scenes, ensure_ascii=False, indent=2))
    print(json.dumps(image_paths, ensure_ascii=False, indent=2))

    # # 方式2：生成 HTML 文件
    # if scenes:
    #     save_html(scenes, "output.html")
    # else:
    #     print("未解析到有效 scenes，已跳过 HTML 生成。")

run()
