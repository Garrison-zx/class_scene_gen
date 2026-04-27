from typing import Optional
from pathlib import Path
import argparse
import base64
import json
import os
import re
from string import Template
import time
import traceback

import requests

MAX_RETRY_ATTEMPTS = 5
RETRY_DELAY_BASE_SECONDS = 5


def _load_local_env_file() -> None:
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
    effective_key = _get_env_value("GOOGLE_API_KEY")
    effective_base_url = _get_env_value("GOOGLE_API_BASE_URL")

    if not effective_key:
        raise ValueError(
            "缺少 API Key，请设置环境变量 GOOGLE_API_KEY。"
        )

    if not effective_base_url:
        raise ValueError(
            "缺少接口地址，请设置环境变量 GOOGLE_API_BASE_URL。"
        )

    return effective_key, effective_base_url


"""构造符合本项目签名的 ai_call 函数。"""
def _ai_call(system: str, user: str, images: Optional[list[dict]] = None) -> str:
    effective_key, effective_base_url = _get_effective_config()
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
            "temperature": 0.1,
            # "responseModalities": ["IMAGE"],  # 同时返回文字 + 图片
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


def _read_prompt(prompt_path: Path, context: Optional[dict] = None) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {prompt_path}")

    prompt_text = prompt_path.read_text(encoding="utf-8")
    if not context:
        return prompt_text

    return Template(prompt_text).safe_substitute(context)


def pipeline(
    context: Optional[dict] = None,
    images: Optional[list[dict]] = None,
    prompt_dir: Optional[Path] = None,
) -> str:
    base_dir = Path(__file__).resolve().parent
    if prompt_dir:
        effective_prompt_dir = prompt_dir
    else:
        # 优先使用当前模块 prompt；不存在时回退到 math_class_gen/prompt
        prompt_candidates = [
            base_dir / "prompt",
            base_dir.parent / "math_class_gen" / "prompt",
        ]
        effective_prompt_dir = next((p for p in prompt_candidates if p.exists()), prompt_candidates[0])

    system_prompt = _read_prompt(
        effective_prompt_dir / "system_gen_class_v1.jinja",
        context=context,
    )
    user_prompt = _read_prompt(
        effective_prompt_dir / "user_gen_class_v1.jinja",
        context=context,
    )

    return _ai_call(system=system_prompt, user=user_prompt, images=images)


def _mime_type_to_suffix(mime_type: str) -> str:
    mime_mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
    }
    return mime_mapping.get(mime_type.lower(), ".bin")


def _save_output_images(response_text: str, output_dir: Path, output_stem: str) -> list[Path]:
    try:
        response_data = json.loads(response_text)
    except json.JSONDecodeError:
        return []

    saved_paths: list[Path] = []
    candidates = response_data.get("candidates", [])
    image_index = 0

    for candidate in candidates:
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        for part in parts:
            inline_data = part.get("inlineData")
            if not inline_data:
                continue

            mime_type = str(inline_data.get("mimeType", "")).strip()
            data = str(inline_data.get("data", "")).strip()
            if not mime_type.startswith("image/") or not data:
                continue

            image_bytes = base64.b64decode(data)
            output_path = output_dir / f"{output_stem}_{image_index}{_mime_type_to_suffix(mime_type)}"
            output_path.write_bytes(image_bytes)
            saved_paths.append(output_path)
            image_index += 1

    return saved_paths


def _extract_output_texts(response_text: str) -> list[str]:
    """提取 Gemini 响应中的文本内容。"""
    try:
        response_data = json.loads(response_text)
    except json.JSONDecodeError:
        raw = response_text.strip()
        return [raw] if raw else []

    texts: list[str] = []
    candidates = response_data.get("candidates", [])
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content", {})
            if not isinstance(content, dict):
                continue
            parts = content.get("parts", [])
            if not isinstance(parts, list):
                continue
            for part in parts:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
    return texts


def _save_output_text_artifacts(response_text: str, output_dir: Path, output_stem: str) -> list[Path]:
    """
    保存文本/代码输出。
    当模型不返回图片时，依然可以保存代码产物。
    """
    texts = _extract_output_texts(response_text)
    if not texts:
        return []

    saved_paths: list[Path] = []
    merged_text = "\n\n".join(texts).strip()
    text_path = output_dir / f"{output_stem}.txt"
    text_path.write_text(merged_text, encoding="utf-8")
    saved_paths.append(text_path)

    code_blocks = re.findall(r"```([A-Za-z0-9_-]*)\s*([\s\S]*?)```", merged_text)
    suffix_map = {
        "json": ".json",
        "javascript": ".js",
        "js": ".js",
        "typescript": ".ts",
        "ts": ".ts",
        "tsx": ".tsx",
        "python": ".py",
        "py": ".py",
        "html": ".html",
        "css": ".css",
        "markdown": ".md",
        "md": ".md",
    }

    for idx, (lang, code) in enumerate(code_blocks, start=1):
        code_content = code.strip()
        if not code_content:
            continue
        extension = suffix_map.get(lang.strip().lower(), ".txt")
        code_path = output_dir / f"{output_stem}.code{idx}{extension}"
        code_path.write_text(code_content, encoding="utf-8")
        saved_paths.append(code_path)

    return saved_paths


def _iter_image_files(image_dir: Path) -> list[Path]:
    supported_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
    return sorted(
        path for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in supported_suffixes
    )


def _collect_input_images(image_input: Path) -> list[Path]:
    supported_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}

    if not image_input.exists():
        raise FileNotFoundError(f"图片输入不存在: {image_input}")

    if image_input.is_dir():
        image_files = _iter_image_files(image_input)
        if not image_files:
            raise FileNotFoundError(f"目录下未找到支持的图片文件: {image_input}")
        return image_files

    if image_input.is_file() and image_input.suffix.lower() in supported_suffixes:
        return [image_input]

    raise ValueError(f"不支持的图片输入: {image_input}")


def _process_single_image(
    image_path: Path,
    output_dir: Path,
    class_script: str,
    output_stem: str,
) -> tuple[bool, Optional[str]]:
    try:
        print(f"正在处理: {output_stem}")
        result = ""
        saved_images: list[Path] = []
        saved_text_artifacts: list[Path] = []
        last_error_message: Optional[str] = None

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            if attempt > 1:
                print(
                    f"重新处理: {output_stem} "
                    f"(第 {attempt} 次尝试，共 {MAX_RETRY_ATTEMPTS} 次)"
                )

            try:
                result = pipeline(
                    context={
                        # "BASELINE_REFERENCE_IMAGE": image_path.name,
                        "CLASS_SCRIPT": class_script,
                    },
                    images=[{"src": str(image_path)}],
                )
                saved_images = _save_output_images(result, output_dir, output_stem)
                saved_text_artifacts = _save_output_text_artifacts(result, output_dir, output_stem)

                if saved_images or saved_text_artifacts:
                    break

                failed_response_path = output_dir / f"{output_stem}_attempt_{attempt}.json"
                failed_response_path.write_text(result, encoding="utf-8")
                last_error_message = "响应中未提取到生成图片或文本代码"
                print(f"未提取到生成图片或文本代码: {output_stem}")
                print(f"失败响应已保存: {failed_response_path}")
            except Exception as exc:
                last_error_message = f"{type(exc).__name__}: {exc}"
                print(f"请求失败: {output_stem} -> {last_error_message}")

            if attempt < MAX_RETRY_ATTEMPTS:
                retry_delay_seconds = RETRY_DELAY_BASE_SECONDS * attempt
                print(f"等待 {retry_delay_seconds}s 后重试: {output_stem}")
                time.sleep(retry_delay_seconds)

        if not saved_images and not saved_text_artifacts:
            raise ValueError(
                last_error_message
                or f"连续 {MAX_RETRY_ATTEMPTS} 次处理均未成功生成图片或文本代码"
            )

        output_path = output_dir / f"{output_stem}.json"
        output_path.write_text(result, encoding="utf-8")
        print(f"处理完成: {output_path}")
        for saved_image in saved_images:
            print(f"已保存图片: {saved_image}")
        for artifact in saved_text_artifacts:
            print(f"已保存文本/代码: {artifact}")
        return True, None
    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        print(f"处理失败: {image_path.name} -> {error_message}")
        error_log_path = output_dir / f"{image_path.stem}.error.log"
        error_log_path.write_text(
            "".join(traceback.format_exception(exc)),
            encoding="utf-8",
        )
        print(f"错误日志: {error_log_path}")
        return False, error_message


def main() -> None:
    _load_local_env_file()
    parser = argparse.ArgumentParser(description="批量处理文件夹中的图片翻译任务")
    parser.add_argument("image_input", type=Path, help="待处理图片目录或单张图片路径")
    parser.add_argument(
        "--class-script",
        type=Path,
        required=True,
        help="课堂剧本文件路径，例如 scene_06_script.md",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="结果输出目录，默认输出到 image_dir/translations",
    )
    args = parser.parse_args()

    image_input = args.image_input.expanduser().resolve()

    class_script_path = args.class_script.expanduser().resolve()
    if not class_script_path.exists() or not class_script_path.is_file():
        raise FileNotFoundError(f"课堂剧本文件不存在: {class_script_path}")
    class_script = class_script_path.read_text(encoding="utf-8")
    class_script_stem = class_script_path.stem

    image_files = _collect_input_images(image_input)

    default_output_base = image_input if image_input.is_dir() else image_input.parent
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir is not None
        else default_output_base / "translations"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    multiple_inputs = len(image_files) > 1
    success_count = 0
    failures: list[tuple[str, str]] = []

    for image_path in image_files:
        output_stem = (
            f"{class_script_stem}_{image_path.stem}"
            if multiple_inputs
            else class_script_stem
        )
        success, error_message = _process_single_image(
            image_path,
            output_dir,
            class_script,
            output_stem,
        )
        if success:
            success_count += 1
            continue
        failures.append((image_path.name, error_message or "未知错误"))

    print(f"批处理完成: 成功 {success_count} 张, 失败 {len(failures)} 张")
    for image_name, error_message in failures:
        print(f"失败文件: {image_name} -> {error_message}")


if __name__ == "__main__":
    main()
