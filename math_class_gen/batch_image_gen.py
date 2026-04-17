"""
batch_image_gen.py - 批量生成 12 个课堂场景图片

遍历 class_materials/ 下所有 scene_XX_script.md，
调用 Gemini 多模态 API（纯文本生成模式），
输出 PNG 图片 + JSON 原始响应 到 generated_images/。

支持断点续跑：已存在图片的场景自动跳过。

运行示例：
    python3 math_class_gen/batch_image_gen.py \\
        --scripts-dir math_class_gen/class_materials \\
        --output-dir math_class_gen/generated_images \\
        --prompt-dir math_class_gen/prompt
"""

import argparse
import base64
import glob
import json
import os
import time
import traceback
from pathlib import Path
from string import Template
from typing import Optional

import requests

MAX_RETRY_ATTEMPTS = 5
RETRY_DELAY_BASE_SECONDS = 5


# ──────────────────────────────────────────────
# 环境配置
# ──────────────────────────────────────────────

def _load_local_env_file() -> None:
    """从脚本同目录的 .env 文件加载环境变量（已存在的不覆盖）。"""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_key = key.strip()
        if not env_key or env_key in os.environ:
            continue
        os.environ[env_key] = value.strip().strip("'").strip('"')


def _get_env_value(*keys: str) -> Optional[str]:
    for key in keys:
        value = os.getenv(key)
        if value and value.strip():
            return value.strip()
    return None


def _get_effective_config() -> tuple[str, str]:
    api_key = _get_env_value("GOOGLE_API_KEY")
    base_url = _get_env_value("GOOGLE_API_BASE_URL")
    if not api_key:
        raise ValueError("缺少 API Key，请设置环境变量 GOOGLE_API_KEY。")
    if not base_url:
        raise ValueError("缺少接口地址，请设置环境变量 GOOGLE_API_BASE_URL。")
    return api_key, base_url


# ──────────────────────────────────────────────
# Prompt 工具
# ──────────────────────────────────────────────

def _read_prompt(prompt_path: Path, context: Optional[dict] = None) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {prompt_path}")
    text = prompt_path.read_text(encoding="utf-8")
    if context:
        text = Template(text).safe_substitute(context)
    return text


# ──────────────────────────────────────────────
# API 调用（纯文本生成模式，不传入图片）
# ──────────────────────────────────────────────

def _ai_call_text_to_image(system: str, user: str) -> str:
    """
    纯文本 → 图片生成：
    不传入任何图片，让模型根据文字描述直接生成课堂场景图。
    responseModalities 包含 IMAGE，要求模型返回图片数据。
    """
    api_key, base_url = _get_effective_config()

    payload = {
        "systemInstruction": {
            "role": "system",
            "parts": [{"text": system}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user}],
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    resp = requests.post(base_url, headers=headers, json=payload, timeout=120)
    print(f"  HTTP {resp.status_code}")
    resp.raise_for_status()

    try:
        data = resp.json()
        return json.dumps(data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        return resp.text


# ──────────────────────────────────────────────
# 图片提取 & 保存
# ──────────────────────────────────────────────

def _mime_to_suffix(mime_type: str) -> str:
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(mime_type.lower(), ".png")


def _extract_and_save_images(
    response_text: str, output_dir: Path, stem: str
) -> list[Path]:
    """从 API 响应中提取 inlineData 图片，保存到 output_dir。"""
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        return []

    saved: list[Path] = []
    idx = 0
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData")
            if not inline:
                continue
            mime = str(inline.get("mimeType", "")).strip()
            raw = str(inline.get("data", "")).strip()
            if not mime.startswith("image/") or not raw:
                continue
            img_bytes = base64.b64decode(raw)
            out_path = output_dir / f"{stem}_{idx}{_mime_to_suffix(mime)}"
            out_path.write_bytes(img_bytes)
            saved.append(out_path)
            idx += 1
    return saved


# ──────────────────────────────────────────────
# 单场景处理
# ──────────────────────────────────────────────

def _process_scene(
    script_path: Path,
    output_dir: Path,
    prompt_dir: Path,
) -> tuple[str, str]:
    """
    处理单个场景剧本，返回 (status, message)。
    status: "ok" | "skip" | "fail"
    """
    stem = script_path.stem  # e.g. scene_05_script

    # 断点续跑：检查输出图片是否已存在
    existing = list(output_dir.glob(f"{stem}_0.*"))
    if existing:
        print(f"  [跳过] {stem}（已存在: {existing[0].name}）")
        return "skip", str(existing[0])

    print(f"  [处理] {stem}")

    # 读取 prompts
    system_prompt = _read_prompt(prompt_dir / "system_gen_class_v1.jinja")
    class_script = script_path.read_text(encoding="utf-8")
    user_prompt = _read_prompt(
        prompt_dir / "user_gen_class_v1.jinja",
        context={"CLASS_SCRIPT": class_script},
    )

    last_error: Optional[str] = None
    saved_images: list[Path] = []
    response_text: str = ""

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        if attempt > 1:
            delay = RETRY_DELAY_BASE_SECONDS * (attempt - 1)
            print(f"    第 {attempt} 次重试，等待 {delay}s ...")
            time.sleep(delay)

        try:
            response_text = _ai_call_text_to_image(system_prompt, user_prompt)
            saved_images = _extract_and_save_images(response_text, output_dir, stem)
            if saved_images:
                break
            # 有响应但没图片
            last_error = "响应中未提取到图片数据"
            fail_path = output_dir / f"{stem}_attempt{attempt}.json"
            fail_path.write_text(response_text, encoding="utf-8")
            print(f"    未提取到图片，响应已保存: {fail_path.name}")
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            print(f"    请求失败: {last_error}")

    if not saved_images:
        err_msg = last_error or f"连续 {MAX_RETRY_ATTEMPTS} 次均失败"
        log_path = output_dir / f"{stem}.error.log"
        log_path.write_text(err_msg + "\n", encoding="utf-8")
        print(f"    [失败] 错误日志: {log_path.name}")
        return "fail", err_msg

    # 保存原始 JSON 响应
    json_path = output_dir / f"{stem}.json"
    json_path.write_text(response_text, encoding="utf-8")
    for img in saved_images:
        print(f"    ✅ 已保存: {img.name}")
    return "ok", str(saved_images[0])


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def main() -> None:
    _load_local_env_file()

    parser = argparse.ArgumentParser(
        description="批量生成课堂场景图片（Gemini 多模态 API）"
    )
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=Path(__file__).parent / "class_materials",
        help="场景剧本目录（默认: math_class_gen/class_materials）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "generated_images",
        help="图片输出目录（默认: math_class_gen/generated_images）",
    )
    parser.add_argument(
        "--prompt-dir",
        type=Path,
        default=Path(__file__).parent / "prompt",
        help="Prompt 模板目录（默认: math_class_gen/prompt）",
    )
    parser.add_argument(
        "--scene",
        type=str,
        default=None,
        help="只处理指定场景，例如 --scene scene_05_script（不含 .md）",
    )
    args = parser.parse_args()

    scripts_dir = args.scripts_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    prompt_dir = args.prompt_dir.expanduser().resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    # 收集场景剧本文件
    if args.scene:
        pattern = str(scripts_dir / f"{args.scene}.md")
        script_files = sorted(Path(p) for p in glob.glob(pattern))
    else:
        script_files = sorted(scripts_dir.glob("scene_*_script.md"))

    if not script_files:
        print(f"未找到场景剧本文件: {scripts_dir}/scene_*_script.md")
        return

    print(f"共找到 {len(script_files)} 个场景剧本")
    print(f"输出目录: {output_dir}")
    print()

    ok_count = skip_count = fail_count = 0
    failures: list[tuple[str, str]] = []

    for script_path in script_files:
        status, msg = _process_scene(script_path, output_dir, prompt_dir)
        if status == "ok":
            ok_count += 1
        elif status == "skip":
            skip_count += 1
        else:
            fail_count += 1
            failures.append((script_path.name, msg))
        print()

    print("=" * 50)
    print(f"批处理完成: 成功 {ok_count} 个，跳过 {skip_count} 个，失败 {fail_count} 个")
    if failures:
        print("\n失败列表:")
        for name, err in failures:
            print(f"  ✗ {name}: {err}")


if __name__ == "__main__":
    main()
