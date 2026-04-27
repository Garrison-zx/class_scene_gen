from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
import uuid
from pathlib import Path
from string import Template
from typing import Any, Optional

import requests

SUBMIT_URL_DEFAULT = (
    "http://api-hub.inner.chj.cloud/"
    "bcs-apihub-tools-proxy-service/tool/v1/supplier/volcengine/"
    "jimeng-i2v-first-tail-v30"
)
RESULT_URL_DEFAULT = (
    "http://api-hub.inner.chj.cloud/"
    "bcs-apihub-tools-proxy-service/tool/v1/supplier/volcengine/"
    "jimeng-i2v-first-tail-v30-result"
)
REQ_KEY_DEFAULT = "jimeng_i2v_first_tail_v30"


def _load_local_env_file() -> None:
    """兼容两级路径：video_generation/.env 与 class_scene_gen/.env。"""
    script_dir = Path(__file__).resolve().parent
    env_candidates = [script_dir / ".env", script_dir.parent / ".env"]

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
    payload = path.read_text(encoding="utf-8") if path.exists() and path.is_file() else raw
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("--vars-json 必须是 JSON 对象")
    return {str(k): str(v) for k, v in data.items()}


def _read_prompt_template(prompt_path: Path, context: Optional[dict[str, str]]) -> str:
    if not prompt_path.exists() or not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt 模板不存在: {prompt_path}")

    prompt_text = prompt_path.read_text(encoding="utf-8")
    if not context:
        return prompt_text.strip()

    rendered = re.sub(
        r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}",
        lambda m: str(context.get(m.group(1), m.group(0))),
        prompt_text,
    )
    return Template(rendered).safe_substitute(context).strip()


def _resolve_prompt(
    *,
    prompt: str,
    prompt_file: str,
    prompt_dir: Path,
    context: Optional[dict[str, str]],
) -> str:
    prompt = (prompt or "").strip()
    if prompt:
        return prompt

    if not prompt_file:
        raise ValueError("提交任务时请提供 --prompt 或 --prompt-file")

    prompt_path = Path(prompt_file)
    if not prompt_path.is_absolute():
        prompt_path = prompt_dir / prompt_path

    final_prompt = _read_prompt_template(prompt_path, context)
    if not final_prompt:
        raise ValueError(f"prompt 内容为空: {prompt_path}")
    return final_prompt


def _read_image_base64(image_path: Path) -> str:
    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(f"图片不存在: {image_path}")

    image_bytes = image_path.read_bytes()
    if not image_bytes:
        raise ValueError(f"图片为空文件: {image_path}")

    return base64.b64encode(image_bytes).decode("utf-8")


def _new_request_id() -> str:
    return str(uuid.uuid4())


def _build_headers(gw_token: str) -> dict[str, str]:
    return {
        "BCS-APIHub-RequestId": _new_request_id(),
        "X-CHJ-GWToken": gw_token,
        "Content-Type": "application/json",
    }


def submit_task(
    *,
    submit_url: str,
    req_key: str,
    gw_token: str,
    prompt: str,
    first_frame: Path,
    tail_frame: Path,
    timeout: float,
) -> dict[str, Any]:
    payload = {
        "req_key": req_key,
        "binary_data_base64": [
            _read_image_base64(first_frame),
            _read_image_base64(tail_frame),
        ],
        "prompt": prompt,
    }

    resp = requests.post(
        submit_url,
        headers=_build_headers(gw_token),
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def query_task(
    *,
    result_url: str,
    req_key: str,
    gw_token: str,
    task_id: str,
    timeout: float,
) -> dict[str, Any]:
    payload = {"req_key": req_key, "task_id": task_id}
    resp = requests.post(
        result_url,
        headers=_build_headers(gw_token),
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def _extract_task_id(resp_json: dict[str, Any]) -> str:
    task_id = str(resp_json.get("data", {}).get("task_id", "")).strip()
    if not task_id:
        raise ValueError(f"提交响应未返回 task_id: {json.dumps(resp_json, ensure_ascii=False)}")
    return task_id


def _extract_status_and_video(resp_json: dict[str, Any]) -> tuple[str, str]:
    data = resp_json.get("data", {})
    status = str(data.get("status", "")).strip().lower()
    video_url = str(data.get("video_url", "")).strip()
    return status, video_url


def _download_video(video_url: str, output_path: Path, timeout: float) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(video_url, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        with output_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def main() -> None:
    _load_local_env_file()

    parser = argparse.ArgumentParser(description="即梦 首尾帧图生视频（提交 + 轮询）")
    parser.add_argument("--first-frame", type=Path, help="首帧图片路径")
    parser.add_argument("--tail-frame", type=Path, help="尾帧图片路径")

    parser.add_argument("--prompt", default="", help="视频提示词（直接文本）")
    parser.add_argument("--prompt-file", default="", help="提示词模板文件（.jinja，默认相对 --prompt-dir）")
    parser.add_argument(
        "--prompt-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "prompt",
        help="提示词目录（默认 class_scene_gen/video_generation/prompt）",
    )
    parser.add_argument("--var", action="append", default=[], help="模板变量 KEY=VALUE，可重复")
    parser.add_argument("--vars-json", default="", help="变量 JSON 字符串或 JSON 文件路径")

    parser.add_argument("--task-id", default="", help="已有 task_id（传入后跳过提交，仅轮询）")

    parser.add_argument("--submit-url", default=os.getenv("JIMENG_I2V_SUBMIT_URL", SUBMIT_URL_DEFAULT))
    parser.add_argument("--result-url", default=os.getenv("JIMENG_I2V_RESULT_URL", RESULT_URL_DEFAULT))
    parser.add_argument("--req-key", default=os.getenv("JIMENG_I2V_REQ_KEY", REQ_KEY_DEFAULT))
    parser.add_argument(
        "--gw-token",
        default=_get_env_value("X_CHJ_GWTOKEN", "X-CHJ-GWToken", "JIMENG_GWTOKEN") or "",
        help="网关 token（也可通过环境变量 X_CHJ_GWTOKEN 提供）",
    )

    parser.add_argument("--poll-interval", type=float, default=2.0, help="轮询间隔秒")
    parser.add_argument("--max-polls", type=int, default=120, help="最大轮询次数")
    parser.add_argument("--request-timeout", type=float, default=30.0, help="单次 HTTP 请求超时秒")

    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "video_generation_outputs")
    parser.add_argument("--save-poll-history", action="store_true", help="保存每次轮询响应")
    parser.add_argument("--download", action="store_true", help="完成后自动下载 mp4")
    parser.add_argument("--output-name", default="", help="下载文件名（默认 task_id.mp4）")

    args = parser.parse_args()

    gw_token = (args.gw_token or "").strip()
    if not gw_token:
        raise ValueError("缺少网关 token，请传 --gw-token 或设置环境变量 X_CHJ_GWTOKEN")

    output_dir: Path = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.task_id.strip():
        task_id = args.task_id.strip()
        submit_resp = {"message": "skip submit by --task-id", "task_id": task_id}
    else:
        if not args.first_frame or not args.tail_frame:
            raise ValueError("提交任务时必须提供 --first-frame 和 --tail-frame")

        context_vars: dict[str, str] = {}
        if args.vars_json:
            context_vars.update(_parse_vars_json(args.vars_json))
        context_vars.update(_parse_kv_items(args.var))

        prompt_text = _resolve_prompt(
            prompt=args.prompt,
            prompt_file=args.prompt_file,
            prompt_dir=args.prompt_dir.expanduser().resolve(),
            context=context_vars,
        )

        submit_resp = submit_task(
            submit_url=args.submit_url,
            req_key=args.req_key,
            gw_token=gw_token,
            prompt=prompt_text,
            first_frame=args.first_frame.expanduser().resolve(),
            tail_frame=args.tail_frame.expanduser().resolve(),
            timeout=args.request_timeout,
        )
        task_id = _extract_task_id(submit_resp)

    submit_path = output_dir / f"{task_id}_submit.json"
    submit_path.write_text(json.dumps(submit_resp, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"task_id: {task_id}")
    print(f"submit_response: {submit_path}")

    final_resp: dict[str, Any] = {}
    done_video_url = ""

    for idx in range(1, args.max_polls + 1):
        resp_json = query_task(
            result_url=args.result_url,
            req_key=args.req_key,
            gw_token=gw_token,
            task_id=task_id,
            timeout=args.request_timeout,
        )
        final_resp = resp_json

        if args.save_poll_history:
            poll_path = output_dir / f"{task_id}_poll_{idx:03d}.json"
            poll_path.write_text(json.dumps(resp_json, ensure_ascii=False, indent=2), encoding="utf-8")

        status, video_url = _extract_status_and_video(resp_json)
        print(f"poll {idx}/{args.max_polls}: status={status or 'unknown'}")

        if video_url:
            done_video_url = video_url
            break

        if status in {"done", "succeeded", "success"}:
            break
        if status in {"failed", "error", "canceled", "cancelled"}:
            break

        time.sleep(args.poll_interval)

    final_path = output_dir / f"{task_id}_final.json"
    final_path.write_text(json.dumps(final_resp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"final_response: {final_path}")

    if done_video_url:
        print(f"video_url: {done_video_url}")
        if args.download:
            filename = args.output_name.strip() or f"{task_id}.mp4"
            video_path = output_dir / filename
            _download_video(done_video_url, video_path, timeout=args.request_timeout)
            print(f"downloaded: {video_path}")
    else:
        print("未拿到 video_url，请检查 final_response。")


if __name__ == "__main__":
    main()
