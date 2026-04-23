"""
Stage 1: 分镜大纲生成。

输入: 课程内容文本 + 风格配置
输出: OutlineResult（包含 VideoOutline 列表）

LLM 根据课程内容自动推断场景数量、类型、时长、旁白和视觉元素。
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

from .types import (
    OutlineResult,
    PipelineConfig,
    SceneType,
    StyleConfig,
    VideoOutline,
)

logger = logging.getLogger(__name__)

# Prompt 模板目录
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    """加载 Prompt 模板文件。"""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt 模板不存在: {path}")
    return path.read_text(encoding="utf-8")


def _build_system_prompt(style: StyleConfig) -> str:
    """构建 Stage 1 的 system prompt。"""
    template = _load_prompt("01_scene_outline_system")
    # 注入风格信息（仅概要，Stage 1 不需要完整风格细节）
    style_summary = json.dumps({
        "name": style.name,
        "description": style.description,
        "canvas": {
            "width": style.canvas_width,
            "height": style.canvas_height,
            "fps": style.fps,
        },
        "colors": style.colors,
    }, ensure_ascii=False, indent=2)

    return template.replace("{{style_summary}}", style_summary)


def _build_user_prompt(
    content: str,
    *,
    target_duration: Optional[float] = None,
    language: str = "zh-CN",
) -> str:
    """构建 Stage 1 的 user prompt。"""
    template = _load_prompt("01_scene_outline_user")
    replacements = {
        "{{content}}": content,
        "{{target_duration}}": str(target_duration or "自动推断"),
        "{{language}}": language,
    }
    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def _parse_json_response(text: str) -> dict[str, Any]:
    """从 LLM 响应中提取 JSON。"""
    # 尝试直接解析
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # 从 code block 中提取
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从 LLM 响应中解析 JSON:\n{text[:500]}")


def _parse_outlines(data: dict[str, Any]) -> OutlineResult:
    """将 LLM 返回的 JSON 解析为 OutlineResult。"""
    language_directive = data.get("languageDirective", "")
    raw_outlines = data.get("outlines", [])

    outlines: list[VideoOutline] = []
    total_duration = 0.0

    for item in raw_outlines:
        scene_type = SceneType(item.get("type", "content"))
        duration = float(item.get("duration_seconds", 5.0))
        total_duration += duration

        outlines.append(VideoOutline(
            id=item.get("id", f"scene_{len(outlines) + 1:02d}"),
            type=scene_type,
            title=item.get("title", ""),
            narration=item.get("narration", ""),
            duration_seconds=duration,
            order=item.get("order", len(outlines) + 1),
            visual_elements=item.get("visual_elements", []),
            animation_hints=item.get("animation_hints", []),
            key_points=item.get("key_points", []),
            code_snippet=item.get("code_snippet"),
            code_language=item.get("code_language"),
        ))

    return OutlineResult(
        language_directive=language_directive,
        outlines=outlines,
        total_duration=total_duration,
    )


# ────────────────────────────────────────────
#  LLM 调用
# ────────────────────────────────────────────

def _call_llm(
    system_prompt: str,
    user_prompt: str,
    config: PipelineConfig,
) -> str:
    """调用 LLM API，返回文本响应。"""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("请安装 openai: pip install openai")

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
        temperature=0.7,
        max_tokens=8192,
    )

    return response.choices[0].message.content or ""


# ────────────────────────────────────────────
#  公开 API
# ────────────────────────────────────────────

def generate_outline(
    content: str,
    config: PipelineConfig,
    *,
    target_duration: Optional[float] = None,
    language: str = "zh-CN",
) -> OutlineResult:
    """
    Stage 1: 生成分镜大纲。

    Args:
        content: 课程内容文本（自然语言描述或结构化大纲）
        config: Pipeline 配置（含 LLM 参数和风格）
        target_duration: 目标视频总时长（秒），None 表示自动推断
        language: 课程语言

    Returns:
        OutlineResult 包含场景列表和元信息
    """
    logger.info("Stage 1: 生成分镜大纲")
    logger.info(f"  内容长度: {len(content)} 字符")
    logger.info(f"  风格: {config.style.name}")
    logger.info(f"  目标时长: {target_duration or '自动推断'}")

    system_prompt = _build_system_prompt(config.style)
    user_prompt = _build_user_prompt(
        content,
        target_duration=target_duration,
        language=language,
    )

    if config.verbose:
        logger.debug(f"System prompt:\n{system_prompt[:500]}...")
        logger.debug(f"User prompt:\n{user_prompt[:500]}...")

    raw_response = _call_llm(system_prompt, user_prompt, config)

    if config.verbose:
        logger.debug(f"LLM response:\n{raw_response[:1000]}...")

    parsed = _parse_json_response(raw_response)
    result = _parse_outlines(parsed)

    logger.info(f"  生成 {len(result.outlines)} 个场景，总时长 {result.total_duration:.0f}s")

    return result
