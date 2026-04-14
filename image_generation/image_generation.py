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
    """
    兼容两级路径：
    1) scripts/image_generation/.env
    2) scripts/.env
    """
    script_dir = Path(__file__).resolve().parent
    env_candidates = [
        script_dir / ".env",
        script_dir.parent / ".env",
    ]

    for env_path in env_candidates:
        if not env_path.exists():
            continue

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
    print("user_content:", user_content)
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


def _read_prompt(prompt_path: Path, context: Optional[dict] = None) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {prompt_path}")

    prompt_text = prompt_path.read_text(encoding="utf-8")
    if not context:
        return prompt_text

    # 兼容两种变量语法：{{VAR}} 与 ${VAR}
    rendered = re.sub(
        r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}",
        lambda m: str(context.get(m.group(1), m.group(0))),
        prompt_text,
    )
    return Template(rendered).safe_substitute(context)


def _parse_kv_items(items: Optional[list[str]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"变量格式错误（需 KEY=VALUE）: {item}")
        key, value = item.split("=", 1)
        k = key.strip()
        if not k:
            raise ValueError(f"变量名不能为空: {item}")
        result[k] = value
    return result


def _parse_vars_json(raw: str) -> dict[str, str]:
    raw = raw.strip()
    if not raw:
        return {}
    path = Path(raw).expanduser()
    if path.exists() and path.is_file():
        payload = path.read_text(encoding="utf-8")
    else:
        payload = raw

    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("--vars-json 必须是 JSON 对象")
    return {str(k): str(v) for k, v in data.items()}


def _resolve_prompt_paths(prompt_dir: Path, prompt_task: str) -> tuple[Path, Path]:
    """
    根据任务标识选择 prompt 文件：
    - default -> system_prompt.jinja / user_prompt.jinja
    - 其他任务 -> system_<task>.jinja / user_<task>.jinja
    兼容误命名场景：若 system_<task>.jinja 不存在，尝试 system_<task>.jinja.jinja
    """
    if prompt_task == "default":
        system_prompt_path = prompt_dir / "system_prompt.jinja"
        user_prompt_path = prompt_dir / "user_prompt.jinja"
        return system_prompt_path, user_prompt_path

    system_prompt_path = prompt_dir / f"system_{prompt_task}.jinja"
    user_prompt_path = prompt_dir / f"user_{prompt_task}.jinja"
    if not system_prompt_path.exists():
        alt = prompt_dir / f"system_{prompt_task}.jinja.jinja"
        if alt.exists():
            system_prompt_path = alt
    return system_prompt_path, user_prompt_path


def pipeline(
    context: Optional[dict] = None,
    images: Optional[list[dict]] = None,
    prompt_dir: Optional[Path] = None,
    prompt_task: str = "default",
) -> str:
    base_dir = Path(__file__).resolve().parent
    effective_prompt_dir = prompt_dir or base_dir / "prompt"
    system_prompt_path, user_prompt_path = _resolve_prompt_paths(effective_prompt_dir, prompt_task)

    system_prompt = _read_prompt(
        system_prompt_path,
        context=context,
    )
    user_prompt = _read_prompt(
        user_prompt_path,
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


def _save_output_images(response_text: str, output_dir: Path, image_stem: str) -> list[Path]:
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
            output_path = output_dir / f"{image_stem}{_mime_type_to_suffix(mime_type)}"
            output_path.write_bytes(image_bytes)
            saved_paths.append(output_path)
            image_index += 1

    return saved_paths


def _iter_image_files(image_dir: Path) -> list[Path]:
    supported_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
    return sorted(
        path for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in supported_suffixes
    )


def _process_single_image(
    image_path: Path,
    output_dir: Path,
    prompt_task: str = "default",
    base_context: Optional[dict[str, str]] = None,
) -> tuple[bool, Optional[str]]:
    try:
        print(f"正在处理: {image_path.name}")
        result = ""
        saved_images: list[Path] = []
        last_error_message: Optional[str] = None

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            if attempt > 1:
                print(
                    f"重新处理: {image_path.name} "
                    f"(第 {attempt} 次尝试，共 {MAX_RETRY_ATTEMPTS} 次)"
                )

            try:
                ctx = dict(base_context or {})
                ctx.update(
                    {
                        "image_name": image_path.name,
                        "image_stem": image_path.stem,
                        "image_ext": image_path.suffix.lstrip("."),
                        "image_path": str(image_path),
                    }
                )
                result = pipeline(
                    context=ctx,
                    images=[{"src": str(image_path)}],
                    prompt_task=prompt_task,
                )
                saved_images = _save_output_images(result, output_dir, image_path.stem)
                if saved_images:
                    break

                last_error_message = "响应中未提取到生成图片"
                print(f"未提取到生成图片: {image_path.name}")
            except Exception as exc:
                last_error_message = f"{type(exc).__name__}: {exc}"
                print(f"请求失败: {image_path.name} -> {last_error_message}")

            if attempt < MAX_RETRY_ATTEMPTS:
                retry_delay_seconds = RETRY_DELAY_BASE_SECONDS * attempt
                print(f"等待 {retry_delay_seconds}s 后重试: {image_path.name}")
                time.sleep(retry_delay_seconds)

        if not saved_images:
            raise ValueError(
                last_error_message
                or f"连续 {MAX_RETRY_ATTEMPTS} 次处理均未成功生成图片"
            )

        output_path = output_dir / f"{image_path.stem}.json"
        output_path.write_text(result, encoding="utf-8")
        print(f"处理完成: {output_path}")
        for saved_image in saved_images:
            print(f"已保存图片: {saved_image}")
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


def _process_without_image(
    output_dir: Path,
    prompt_task: str = "default",
    base_context: Optional[dict[str, str]] = None,
    output_stem: str = "generated_cover",
) -> tuple[bool, Optional[str]]:
    try:
        print("正在处理: 无输入图片模式")
        result = ""
        saved_images: list[Path] = []
        last_error_message: Optional[str] = None

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            if attempt > 1:
                print(
                    f"重新处理: 无输入图片模式 "
                    f"(第 {attempt} 次尝试，共 {MAX_RETRY_ATTEMPTS} 次)"
                )

            try:
                ctx = dict(base_context or {})
                result = pipeline(
                    context=ctx,
                    images=None,
                    prompt_task=prompt_task,
                )
                saved_images = _save_output_images(result, output_dir, output_stem)
                if saved_images:
                    break

                last_error_message = "响应中未提取到生成图片"
                print("未提取到生成图片: 无输入图片模式")
            except Exception as exc:
                last_error_message = f"{type(exc).__name__}: {exc}"
                print(f"请求失败: 无输入图片模式 -> {last_error_message}")

            if attempt < MAX_RETRY_ATTEMPTS:
                retry_delay_seconds = RETRY_DELAY_BASE_SECONDS * attempt
                print(f"等待 {retry_delay_seconds}s 后重试: 无输入图片模式")
                time.sleep(retry_delay_seconds)

        if not saved_images:
            raise ValueError(
                last_error_message
                or f"连续 {MAX_RETRY_ATTEMPTS} 次处理均未成功生成图片"
            )

        output_path = output_dir / f"{output_stem}.json"
        output_path.write_text(result, encoding="utf-8")
        print(f"处理完成: {output_path}")
        for saved_image in saved_images:
            print(f"已保存图片: {saved_image}")
        return True, None
    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        print(f"处理失败: 无输入图片模式 -> {error_message}")
        error_log_path = output_dir / f"{output_stem}.error.log"
        error_log_path.write_text(
            "".join(traceback.format_exception(exc)),
            encoding="utf-8",
        )
        print(f"错误日志: {error_log_path}")
        return False, error_message


def main() -> None:
    _load_local_env_file()
    parser = argparse.ArgumentParser(description="批量执行图像生成任务")
    parser.add_argument(
        "image_dir",
        type=Path,
        nargs="?",
        default=None,
        help="待处理图片目录。封面生成等不依赖输入图的任务可省略此参数",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="结果输出目录，默认输出到 image_dir/translations",
    )
    parser.add_argument(
        "--prompt-task",
        default="default",
        help=(
            "提示词任务标识。"
            "default -> system_prompt.jinja + user_prompt.jinja；"
            "例如 img_trans_ja -> system_img_trans_ja.jinja + user_img_trans_ja.jinja；"
            "cover_img_gen -> system_cover_img_gen.jinja + user_cover_img_gen.jinja"
        ),
    )
    parser.add_argument(
        "--var",
        action="append",
        default=[],
        help="注入模板变量，可重复传入。格式 KEY=VALUE，例如 COURSE_THEME=工业AI转型",
    )
    parser.add_argument(
        "--vars-json",
        default="",
        help="批量变量（JSON 字符串或 JSON 文件路径），与 --var 合并，后者优先",
    )
    parser.add_argument(
        "--allow-no-input",
        action="store_true",
        help="允许目录中无图片时也执行生成（适用于封面图等不依赖输入图的任务）",
    )
    parser.add_argument(
        "--no-input-stem",
        default="generated_cover",
        help="无输入图片模式下的输出文件名前缀（默认: generated_cover）",
    )
    args = parser.parse_args()

    # image_dir 未指定时自动进入无输入图模式
    if args.image_dir is None:
        if args.output_dir is None:
            args.output_dir = Path.cwd()
        args.allow_no_input = True
        image_dir = args.output_dir.expanduser().resolve()
    else:
        image_dir = args.image_dir.expanduser().resolve()
        if not image_dir.exists() or not image_dir.is_dir():
            raise NotADirectoryError(f"图片目录不存在: {image_dir}")

    image_files = [] if args.image_dir is None else _iter_image_files(image_dir)

    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir is not None
        else image_dir / "translations"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    context_vars = {}
    if args.vars_json:
        context_vars.update(_parse_vars_json(args.vars_json))
    context_vars.update(_parse_kv_items(args.var))

    success_count = 0
    failures: list[tuple[str, str]] = []

    if not image_files:
        if not args.allow_no_input:
            raise FileNotFoundError(
                f"目录下未找到支持的图片文件: {image_dir}。"
                "若当前任务不依赖输入图，请增加 --allow-no-input。"
            )
        success, error_message = _process_without_image(
            output_dir=output_dir,
            prompt_task=args.prompt_task,
            base_context=context_vars,
            output_stem=args.no_input_stem,
        )
        if success:
            success_count += 1
        else:
            failures.append((args.no_input_stem, error_message or "未知错误"))
    else:
        for image_path in image_files:
            success, error_message = _process_single_image(
                image_path=image_path,
                output_dir=output_dir,
                prompt_task=args.prompt_task,
                base_context=context_vars,
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
