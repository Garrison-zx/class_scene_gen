"""
冒烟测试：类型定义 + 风格加载。
"""

import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.types import (
    StyleConfig,
    VideoOutline,
    SceneType,
    OutlineResult,
    SceneCode,
    PipelineConfig,
)


def test_style_config_default():
    """默认风格配置。"""
    style = StyleConfig()
    assert style.name == "default"
    assert style.canvas_width == 1920
    assert style.canvas_height == 1080
    assert style.fps == 30
    assert "background" in style.colors
    assert "titleFont" in style.typography
    print("  ✅ StyleConfig 默认值")


def test_style_config_from_json():
    """从 JSON 加载风格。"""
    data = {
        "name": "test-style",
        "description": "测试风格",
        "canvas": {"width": 1280, "height": 720, "fps": 60},
        "colors": {"background": "#000", "primary": "#FFF", "accent": "#F00"},
        "typography": {"titleFont": "Arial", "titleSize": 48},
    }
    style = StyleConfig.from_json(data)
    assert style.name == "test-style"
    assert style.canvas_width == 1280
    assert style.fps == 60
    assert style.colors["background"] == "#000"
    assert style.raw_json == data
    print("  ✅ StyleConfig.from_json")


def test_style_config_from_file():
    """从文件加载风格。"""
    styles_dir = Path(__file__).resolve().parent.parent / "styles"

    for style_file in styles_dir.glob("*.json"):
        style = StyleConfig.from_file(style_file)
        assert style.name, f"{style_file.name} missing name"
        assert style.canvas_width > 0
        assert style.fps > 0
        assert "background" in style.colors
        print(f"  ✅ {style_file.name} → {style.name}")


def test_video_outline():
    """VideoOutline 创建。"""
    outline = VideoOutline(
        id="scene_01",
        type=SceneType.TITLE,
        title="测试标题",
        narration="这是测试旁白",
        duration_seconds=5.0,
        order=1,
        visual_elements=["大标题", "副标题"],
        animation_hints=["淡入"],
    )
    assert outline.id == "scene_01"
    assert outline.type == SceneType.TITLE
    assert outline.duration_seconds == 5.0
    print("  ✅ VideoOutline 创建")


def test_scene_code():
    """SceneCode 创建。"""
    code = SceneCode(
        scene_id="scene_01",
        component_name="Scene01Title",
        code='export const Scene01Title = () => <div>Hello</div>;',
        duration_frames=150,
    )
    assert code.component_name == "Scene01Title"
    assert code.duration_frames == 150
    print("  ✅ SceneCode 创建")


def test_outline_result():
    """OutlineResult 创建。"""
    result = OutlineResult(
        language_directive="使用中文",
        outlines=[
            VideoOutline(
                id="scene_01", type=SceneType.TITLE, title="标题",
                narration="旁白", duration_seconds=4.0, order=1,
            ),
            VideoOutline(
                id="scene_02", type=SceneType.CONTENT, title="内容",
                narration="旁白2", duration_seconds=10.0, order=2,
            ),
        ],
        total_duration=14.0,
    )
    assert len(result.outlines) == 2
    assert result.total_duration == 14.0
    print("  ✅ OutlineResult 创建")


def test_pipeline_config():
    """PipelineConfig 创建。"""
    config = PipelineConfig()
    assert config.style.name == "default"
    assert config.llm_model == "gpt-4o"
    assert not config.enable_tts
    print("  ✅ PipelineConfig 默认值")


def test_prompt_files_exist():
    """检查 Prompt 模板文件存在。"""
    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    required = [
        "01_scene_outline_system.md",
        "01_scene_outline_user.md",
        "02_remotion_scene_system.md",
        "02_remotion_scene_user.md",
    ]
    for name in required:
        path = prompts_dir / name
        assert path.exists(), f"缺少 Prompt: {path}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 100, f"Prompt 内容过短: {path}"
        print(f"  ✅ {name} ({len(content)} 字符)")


if __name__ == "__main__":
    print("🧪 视频生成 Pipeline 冒烟测试\n")

    tests = [
        test_style_config_default,
        test_style_config_from_json,
        test_style_config_from_file,
        test_video_outline,
        test_scene_code,
        test_outline_result,
        test_pipeline_config,
        test_prompt_files_exist,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            print(f"=== {test.__name__} ===")
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"通过: {passed}, 失败: {failed}")
    if failed > 0:
        sys.exit(1)
