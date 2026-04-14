#!/usr/bin/env python3
"""即梦文生视频调用脚本。

用法（只需要给提示词）：
1) 直接给文本：
   python text2video.py --prompt "一只猫在太空中跳舞"

2) 从 prompt 目录读取文件：
   python text2video.py --prompt-file my_prompt.txt

环境变量从同目录 `.env` 自动读取：
- JIMENG_URL: 接口地址
- JIMENG_SECRET: 密钥
- JIMENG_METHOD: 请求方法，默认 POST
- JIMENG_AUTH_HEADER: 鉴权头名，默认 Authorization
- JIMENG_AUTH_PREFIX: 鉴权前缀，默认 Bearer
- JIMENG_EXTRA_HEADERS: 额外请求头 JSON，默认 {}
- JIMENG_BODY_TEMPLATE: 请求体模板 JSON，默认 {"prompt":"{{prompt}}"}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
PROMPT_DIR = BASE_DIR / "prompt"


def load_env_file(env_path: Path) -> None:
    """读取 .env 到进程环境（不覆盖已有环境变量）。"""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"missing env: {name}")
    return value


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt and args.prompt.strip():
        return args.prompt.strip()

    if not args.prompt_file:
        raise ValueError("请提供 --prompt 或 --prompt-file")

    prompt_path = Path(args.prompt_file)
    if not prompt_path.is_absolute():
        prompt_path = PROMPT_DIR / prompt_path

    if not prompt_path.exists() or not prompt_path.is_file():
        raise FileNotFoundError(f"prompt 文件不存在: {prompt_path}")

    text = prompt_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"prompt 文件为空: {prompt_path}")
    return text


def parse_json_env(name: str, default: Dict[str, Any]) -> Dict[str, Any]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return dict(default)
    try:
        data = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"env {name} 不是合法 JSON") from exc
    if not isinstance(data, dict):
        raise ValueError(f"env {name} 必须是 JSON 对象")
    return data


def inject_prompt(template: Any, prompt: str) -> Any:
    """将模板中的 '{{prompt}}' 递归替换为真实提示词。"""
    if isinstance(template, str):
        return template.replace("{{prompt}}", prompt)
    if isinstance(template, list):
        return [inject_prompt(x, prompt) for x in template]
    if isinstance(template, dict):
        return {k: inject_prompt(v, prompt) for k, v in template.items()}
    return template


def build_request(prompt: str) -> Dict[str, Any]:
    url = require_env("JIMENG_URL")
    secret = require_env("JIMENG_SECRET")
    method = os.getenv("JIMENG_METHOD", "POST").strip().upper() or "POST"

    auth_header = os.getenv("JIMENG_AUTH_HEADER", "Authorization").strip() or "Authorization"
    auth_prefix = os.getenv("JIMENG_AUTH_PREFIX", "Bearer").strip()

    headers = parse_json_env("JIMENG_EXTRA_HEADERS", {})
    headers.setdefault("Content-Type", "application/json")
    headers[auth_header] = f"{auth_prefix} {secret}".strip() if auth_prefix else secret

    body_template = parse_json_env("JIMENG_BODY_TEMPLATE", {"prompt": "{{prompt}}"})
    body = inject_prompt(body_template, prompt)

    return {"url": url, "method": method, "headers": headers, "body": body}


def request_api(url: str, method: str, headers: Dict[str, str], body: Dict[str, Any], timeout: Optional[float]) -> Dict[str, Any]:
    import requests

    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        raise ValueError(f"不支持的方法: {method}")

    resp = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=body if method != "GET" else None,
        params=body if method == "GET" else None,
        timeout=timeout,
    )

    try:
        data = resp.json()
    except Exception:
        data = {"raw_text": resp.text}

    return {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "data": data,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="即梦文生视频调用")
    p.add_argument("--prompt", default="", help="直接传入提示词")
    p.add_argument(
        "--prompt-file",
        default="",
        help="提示词文件名（相对 prompt 目录）或绝对路径",
    )
    p.add_argument("--timeout", type=float, default=None, help="请求超时（秒），默认不限时")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印最终请求参数，不发请求",
    )
    return p


def main() -> int:
    load_env_file(ENV_PATH)
    args = build_parser().parse_args()

    prompt = read_prompt(args)
    req = build_request(prompt)

    if args.dry_run:
        masked = dict(req)
        h = dict(masked["headers"])
        if "Authorization" in h:
            h["Authorization"] = "***"
        masked["headers"] = h
        print(json.dumps(masked, ensure_ascii=False, indent=2))
        return 0

    result = request_api(
        url=req["url"],
        method=req["method"],
        headers=req["headers"],
        body=req["body"],
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
