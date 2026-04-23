"""
Stage 2: Remotion 场景代码生成。

输入: VideoOutline + StyleConfig
输出: SceneCode（包含 .tsx 组件代码）

每个场景独立生成一个 Remotion React 组件，
风格配置（style.json）以结构化 Token 注入 Prompt，确保所有场景视觉一致。
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from .types import (
    PipelineConfig,
    SceneCode,
    StyleConfig,
    VideoOutline,
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt 模板不存在: {path}")
    return path.read_text(encoding="utf-8")


def _build_system_prompt(style: StyleConfig) -> str:
    """构建 Stage 2 的 system prompt。

    将完整的 style.json 注入 Prompt，
    LLM 必须严格遵循其中的配色/排版/动画/组件样式。
    """
    template = _load_prompt("02_remotion_scene_system")

    style_json = json.dumps(
        style.raw_json if style.raw_json else {
            "name": style.name,
            "canvas": {
                "width": style.canvas_width,
                "height": style.canvas_height,
                "fps": style.fps,
            },
            "colors": style.colors,
            "typography": style.typography,
            "layout": style.layout,
            "animations": style.animations,
            "components": style.components,
            "transitions": style.transitions,
        },
        ensure_ascii=False,
        indent=2,
    )

    return template.replace("{{style_config}}", style_json)


def _build_user_prompt(outline: VideoOutline, style: StyleConfig) -> str:
    """构建单个场景的 user prompt。"""
    template = _load_prompt("02_remotion_scene_user")

    replacements = {
        "{{scene_id}}": outline.id,
        "{{scene_type}}": outline.type.value,
        "{{title}}": outline.title,
        "{{narration}}": outline.narration,
        "{{duration_seconds}}": str(outline.duration_seconds),
        "{{duration_frames}}": str(int(outline.duration_seconds * style.fps)),
        "{{visual_elements}}": "\n".join(f"- {v}" for v in outline.visual_elements) or "（无）",
        "{{animation_hints}}": "\n".join(f"- {a}" for a in outline.animation_hints) or "（无）",
        "{{key_points}}": "\n".join(f"- {k}" for k in outline.key_points) or "（无）",
        "{{code_snippet}}": outline.code_snippet or "（无）",
        "{{code_language}}": outline.code_language or "（无）",
        "{{fps}}": str(style.fps),
    }

    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def _extract_tsx_code(response: str) -> str:
    """从 LLM 响应中提取 TSX 代码。"""
    # 策略 1: tsx code block
    match = re.search(r"```(?:tsx|typescript|ts)\s*([\s\S]*?)```", response)
    if match:
        return match.group(1).strip()

    # 策略 2: 任意 code block
    match = re.search(r"```\s*([\s\S]*?)```", response)
    if match:
        code = match.group(1).strip()
        if "import" in code and "export" in code:
            return code

    # 策略 3: 整个响应看起来就是代码
    stripped = response.strip()
    if stripped.startswith("import") or stripped.startswith("//"):
        return stripped

    raise ValueError(f"无法从 LLM 响应中提取 TSX 代码:\n{response[:500]}")


def _make_component_name(outline: VideoOutline) -> str:
    """生成 React 组件名。"""
    # scene_01 → Scene01, scene_02_title → Scene02Title
    parts = outline.id.split("_")
    name = "".join(p.capitalize() for p in parts)
    # 追加类型后缀
    type_suffix = outline.type.value.capitalize()
    return f"{name}{type_suffix}"


def _call_llm(
    system_prompt: str,
    user_prompt: str,
    config: PipelineConfig,
) -> str:
    """调用 LLM API。"""
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
        temperature=0.4,      # 代码生成用较低温度
        max_tokens=16384,      # 组件代码可能较长
    )

    return response.choices[0].message.content or ""


# ────────────────────────────────────────────
#  公开 API
# ────────────────────────────────────────────

def generate_scene_code(
    outline: VideoOutline,
    config: PipelineConfig,
) -> SceneCode:
    """
    为单个场景生成 Remotion 组件代码。

    Args:
        outline: 场景大纲
        config: Pipeline 配置

    Returns:
        SceneCode 包含组件名和 TSX 代码
    """
    component_name = _make_component_name(outline)
    logger.info(f"  Stage 2: 生成 {component_name} ({outline.type.value})")

    system_prompt = _build_system_prompt(config.style)
    user_prompt = _build_user_prompt(outline, config.style)

    if config.verbose:
        logger.debug(f"System prompt (前 500 字):\n{system_prompt[:500]}...")
        logger.debug(f"User prompt:\n{user_prompt[:500]}...")

    raw_response = _call_llm(system_prompt, user_prompt, config)
    code = _extract_tsx_code(raw_response)

    duration_frames = int(outline.duration_seconds * config.style.fps)

    return SceneCode(
        scene_id=outline.id,
        component_name=component_name,
        code=code,
        duration_frames=duration_frames,
    )


def generate_all_scenes(
    outlines: list[VideoOutline],
    config: PipelineConfig,
) -> list[SceneCode]:
    """
    批量生成所有场景的 Remotion 组件代码。

    Args:
        outlines: 场景大纲列表
        config: Pipeline 配置

    Returns:
        SceneCode 列表，顺序与输入一致
    """
    logger.info(f"Stage 2: 批量生成 {len(outlines)} 个场景")

    scenes: list[SceneCode] = []
    for outline in outlines:
        scene = generate_scene_code(outline, config)
        scenes.append(scene)
        logger.info(f"    ✅ {scene.component_name} ({scene.duration_frames} frames)")

    return scenes
