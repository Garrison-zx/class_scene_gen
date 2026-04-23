"""
类型定义 — 文/图生视频 Pipeline 的核心数据结构。

三层结构：
1. VideoOutline  — Stage 1 输出的分镜大纲
2. SceneCode     — Stage 2 输出的 Remotion 组件代码
3. StyleConfig   — 风格配置（JSON 注入 Prompt）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ────────────────────────────────────────────
#  场景类型
# ────────────────────────────────────────────

class SceneType(str, Enum):
    """视频场景类型。"""
    TITLE = "title"              # 标题页
    CONTENT = "content"          # 正文内容页
    DIAGRAM = "diagram"          # 流程图 / 架构图
    CODE = "code"                # 代码演示
    QUIZ = "quiz"                # 测验 / 问答
    TRANSITION = "transition"    # 过渡页
    SUMMARY = "summary"          # 总结页


# ────────────────────────────────────────────
#  Stage 1: 分镜大纲
# ────────────────────────────────────────────

@dataclass
class VideoOutline:
    """
    单个分镜场景的大纲。

    由 Stage 1（outline-generator）的 LLM 生成，
    描述一个场景应该"展示什么内容、讲什么旁白、持续多久"。
    """
    id: str                                      # 唯一标识，如 scene_01
    type: SceneType                              # 场景类型
    title: str                                   # 场景标题
    narration: str                               # 旁白文本（TTS 用）
    duration_seconds: float                      # 时长（秒）
    order: int                                   # 排列顺序（从 1 开始）
    visual_elements: list[str] = field(default_factory=list)   # 视觉元素描述
    animation_hints: list[str] = field(default_factory=list)   # 动画提示
    key_points: list[str] = field(default_factory=list)        # 核心知识点
    code_snippet: Optional[str] = None           # 代码片段（type=code 时）
    code_language: Optional[str] = None          # 代码语言（type=code 时）


@dataclass
class OutlineResult:
    """Stage 1 完整输出。"""
    language_directive: str                      # 语言指令
    outlines: list[VideoOutline]                 # 场景列表
    total_duration: float = 0.0                  # 总时长（秒）
    metadata: dict[str, Any] = field(default_factory=dict)


# ────────────────────────────────────────────
#  Stage 2: Remotion 组件代码
# ────────────────────────────────────────────

@dataclass
class SceneCode:
    """
    Stage 2 输出：一个场景对应的 Remotion 组件代码。
    """
    scene_id: str                  # 对应 VideoOutline.id
    component_name: str            # React 组件名，如 Scene01Title
    code: str                      # 完整的 .tsx 文件内容
    duration_frames: int           # 帧数（= duration_seconds × fps）


# ────────────────────────────────────────────
#  风格配置
# ────────────────────────────────────────────

@dataclass
class StyleConfig:
    """
    风格配置文件的 Python 映射。

    JSON 文件原样注入 Prompt，这里做类型校验和默认值。
    """
    name: str = "default"
    description: str = ""

    # 画布
    canvas_width: int = 1920
    canvas_height: int = 1080
    fps: int = 30

    # 配色
    colors: dict[str, str] = field(default_factory=lambda: {
        "background": "#1A1A2E",
        "primary": "#FFFFFF",
        "secondary": "#A0A0B0",
        "accent": "#0F83F5",
        "text": "#F0F0F0",
        "textSecondary": "#A0A0B0",
    })

    # 排版
    typography: dict[str, Any] = field(default_factory=lambda: {
        "titleFont": "Inter",
        "titleSize": 64,
        "titleWeight": 700,
        "bodyFont": "Inter",
        "bodySize": 28,
        "bodyWeight": 400,
        "codeFont": "JetBrains Mono",
        "lineHeight": 1.5,
    })

    # 布局
    layout: dict[str, Any] = field(default_factory=lambda: {
        "padding": {"top": 100, "bottom": 100, "left": 120, "right": 120},
        "titlePosition": "center",
        "contentAlignment": "left",
        "maxContentWidth": 1400,
    })

    # 动画
    animations: dict[str, Any] = field(default_factory=lambda: {
        "enterType": "fadeIn",
        "enterDuration": 20,
        "exitType": "fadeOut",
        "exitDuration": 15,
        "stagger": 5,
        "easing": "easeInOutCubic",
    })

    # 组件样式
    components: dict[str, Any] = field(default_factory=dict)

    # 场景过渡
    transitions: dict[str, Any] = field(default_factory=lambda: {
        "between_scenes": "crossfade",
        "duration": 15,
    })

    # 原始 JSON（注入 Prompt 时直接用）
    raw_json: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "StyleConfig":
        """从 JSON 字典构建 StyleConfig。"""
        canvas = data.get("canvas", {})
        defaults = cls()  # 获取默认值实例
        return cls(
            name=data.get("name", "custom"),
            description=data.get("description", ""),
            canvas_width=canvas.get("width", 1920),
            canvas_height=canvas.get("height", 1080),
            fps=canvas.get("fps", 30),
            colors=data.get("colors", defaults.colors),
            typography=data.get("typography", defaults.typography),
            layout=data.get("layout", defaults.layout),
            animations=data.get("animations", defaults.animations),
            components=data.get("components", {}),
            transitions=data.get("transitions", defaults.transitions),
            raw_json=data,
        )

    @classmethod
    def from_file(cls, path: Path) -> "StyleConfig":
        """从 JSON 文件加载风格配置。"""
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_json(data)


# ────────────────────────────────────────────
#  Pipeline 配置
# ────────────────────────────────────────────

@dataclass
class PipelineConfig:
    """Pipeline 运行参数。"""
    style: StyleConfig = field(default_factory=StyleConfig)
    output_dir: Path = Path("./output")
    enable_tts: bool = False
    tts_provider: str = "edge-tts"          # edge-tts | volcengine
    llm_provider: str = "openai"            # openai | volcengine | local
    llm_model: str = "gpt-4o"
    llm_api_key: str = ""
    llm_base_url: str = ""
    verbose: bool = False
