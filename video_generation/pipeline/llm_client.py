"""
LLM 客户端封装。

支持两种调用模式：
1. OpenAI Chat Completions 兼容接口（原有方式）
2. Gemini generateContent 接口（参考 math_class_gen_v1.py）
"""

from __future__ import annotations

import json
from typing import Any

import requests

from .types import PipelineConfig


def _should_use_gemini_generate_content(config: PipelineConfig) -> bool:
    base_url = (config.llm_base_url or "").strip()
    provider = (config.llm_provider or "").strip().lower()

    if provider == "gemini":
        return True

    if not base_url:
        return False

    if "chat/completions" in base_url:
        return False

    gemini_markers = (
        "generativelanguage.googleapis.com",
        "/v1beta/models",
        ":generateContent",
        "/models/",
    )
    return any(marker in base_url for marker in gemini_markers)


def _build_gemini_generate_content_url(base_url: str, model: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise ValueError("Gemini 模式下 llm_base_url 不能为空。")
    if not model:
        raise ValueError("Gemini 模式下 llm_model 不能为空。")

    if ":generateContent" in base:
        return base

    if base.endswith("/models"):
        return f"{base}/{model}:generateContent"

    if "/models/" in base:
        tail = base.split("/models/", 1)[1]
        if tail == model:
            return f"{base}:generateContent"
        return f"{base}/{model}:generateContent"

    if base.endswith("/v1beta") or base.endswith("/v1"):
        return f"{base}/models/{model}:generateContent"

    return f"{base}/v1beta/models/{model}:generateContent"


def _extract_text_from_gemini_response(data: dict[str, Any]) -> str:
    texts: list[str] = []
    candidates = data.get("candidates", [])
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
                    texts.append(text)

    if texts:
        return "\n".join(texts).strip()

    # 兼容部分网关返回 OpenAI 结构
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message", {})
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content

    raise ValueError(
        "Gemini 响应中未找到文本内容。"
        f" keys={list(data.keys())}"
    )


def _call_gemini_generate_content(
    *,
    system_prompt: str,
    user_prompt: str,
    config: PipelineConfig,
    temperature: float,
    max_tokens: int,
) -> str:
    url = _build_gemini_generate_content_url(config.llm_base_url, config.llm_model)

    payload = {
        "systemInstruction": {
            "role": "system",
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
        },
    }
    if max_tokens > 0:
        payload["generationConfig"]["maxOutputTokens"] = max_tokens

    headers = {
        "x-goog-api-key": config.llm_api_key,
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise ValueError(f"Gemini 返回非 JSON 响应: {resp.text[:500]}")

    # 兼容网关统一错误结构
    if data.get("success") is False:
        code = data.get("code")
        msg = data.get("msg", "unknown gateway error")
        raise PermissionError(f"Gemini 网关调用失败(code={code}): {msg}")

    if "error" in data:
        raise RuntimeError(f"Gemini 调用失败: {json.dumps(data['error'], ensure_ascii=False)}")

    return _extract_text_from_gemini_response(data)


def _call_openai_chat(
    *,
    system_prompt: str,
    user_prompt: str,
    config: PipelineConfig,
    temperature: float,
    max_tokens: int,
) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("请安装 openai: pip install openai") from exc

    client = OpenAI(
        api_key=config.llm_api_key,
        base_url=config.llm_base_url or None,
    )

    response = client.chat.completions.create(
        model=config.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    choices = getattr(response, "choices", None)
    if not choices:
        raise ValueError("LLM 返回为空 choices，可能是网关返回结构与 OpenAI SDK 不兼容。")

    content = choices[0].message.content
    if not content:
        raise ValueError("LLM 返回 message.content 为空。")
    return content


def call_llm_text(
    *,
    system_prompt: str,
    user_prompt: str,
    config: PipelineConfig,
    temperature: float,
    max_tokens: int,
) -> str:
    """统一文本调用入口。"""
    if _should_use_gemini_generate_content(config):
        return _call_gemini_generate_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            config=config,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return _call_openai_chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        config=config,
        temperature=temperature,
        max_tokens=max_tokens,
    )
