"""
Pipeline Runner — 串联 Stage 1 → 2 → 3 的主入口。

用法：
    python -m pipeline.runner --content "xxx" --style styles/apple-keynote.json
    python -m pipeline.runner --content-file input.md --style styles/tech-dark.json --render
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Optional

from .types import PipelineConfig, StyleConfig
from .outline_generator import generate_outline
from .scene_generator import generate_all_scenes
from .assembler import (
    write_scene_files,
    generate_root_tsx,
    render_video,
    save_outline_json,
    synthesize_narration_audio,
)

logger = logging.getLogger(__name__)


def run_pipeline(
    content: str,
    config: PipelineConfig,
    *,
    target_duration: Optional[float] = None,
    language: str = "zh-CN",
    skip_render: bool = True,
) -> dict:
    """
    执行完整的 Pipeline。

    Args:
        content: 课程内容
        config: Pipeline 配置
        target_duration: 目标时长（秒）
        language: 课程语言
        skip_render: 是否跳过渲染（默认跳过，仅生成代码）

    Returns:
        结果字典，包含各阶段输出
    """
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "stages": {},
        "output_dir": str(output_dir),
    }

    # ── Stage 1: 分镜大纲 ──
    logger.info("=" * 60)
    logger.info("🎬 Stage 1: 分镜大纲生成")
    logger.info("=" * 60)

    outline_result = generate_outline(
        content,
        config,
        target_duration=target_duration,
        language=language,
    )

    outline_path = save_outline_json(outline_result, output_dir)
    result["stages"]["outline"] = {
        "scene_count": len(outline_result.outlines),
        "total_duration": outline_result.total_duration,
        "output": str(outline_path),
    }

    # ── Stage 2: Remotion 组件代码生成 ──
    logger.info("")
    logger.info("=" * 60)
    logger.info("🎨 Stage 2: Remotion 组件代码生成")
    logger.info("=" * 60)

    scene_codes = generate_all_scenes(outline_result.outlines, config)

    generated_dir = output_dir / "generated"
    scene_paths = write_scene_files(scene_codes, generated_dir)
    result["stages"]["scene_code"] = {
        "scene_count": len(scene_codes),
        "files": [str(p) for p in scene_paths],
    }

    # ── Stage 3: TTS（可选） ──
    scene_audio_map: dict[str, str] = {}
    if config.enable_tts:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🔊 Stage 3: TTS 音频生成 (Doubao)")
        logger.info("=" * 60)
        try:
            scene_audio_map, tts_summary = synthesize_narration_audio(
                outline_result.outlines,
                config,
                output_dir,
            )

            # 用真实音频时长回写场景帧长，避免音频被 Sequence 截断
            duration_ms_map: dict[str, int] = {}
            for item in tts_summary.get("items", []):
                try:
                    scene_id = str(item.get("scene_id", "")).strip()
                    duration_ms = int(item.get("duration_ms", 0))
                except Exception:  # noqa: BLE001
                    continue
                if scene_id and duration_ms > 0:
                    duration_ms_map[scene_id] = duration_ms

            if duration_ms_map:
                fps = int(config.style.fps)
                padding_ms = max(0, int(config.tts_padding_ms))
                alignment_items: list[dict[str, int]] = []
                for scene in scene_codes:
                    audio_ms = duration_ms_map.get(scene.scene_id, 0)
                    if audio_ms <= 0:
                        continue
                    aligned_frames = math.ceil((audio_ms + padding_ms) / 1000 * fps)
                    old_frames = int(scene.duration_frames)
                    new_frames = max(old_frames, aligned_frames)
                    if new_frames != old_frames:
                        scene.duration_frames = new_frames
                    alignment_items.append(
                        {
                            "scene_id": scene.scene_id,
                            "audio_ms": audio_ms,
                            "old_frames": old_frames,
                            "new_frames": new_frames,
                        }
                    )

                tts_summary["padding_ms"] = padding_ms
                tts_summary["duration_alignment"] = alignment_items
            result["stages"]["tts"] = tts_summary
        except Exception as e:
            logger.error(f"TTS 失败: {e}")
            result["stages"]["tts"] = {
                "error": str(e),
            }
    else:
        logger.info("\n⏭️  跳过 TTS（使用 --enable-tts 启用）")

    # ── Stage 4: 组装 ──
    logger.info("")
    logger.info("=" * 60)
    logger.info("🔧 Stage 4: 组装")
    logger.info("=" * 60)

    root_path = generate_root_tsx(
        scene_codes,
        outline_result.outlines,
        fps=config.style.fps,
        scene_audio_map=scene_audio_map,
        output_dir=output_dir,
    )
    result["stages"]["assemble"] = {
        "root_tsx": str(root_path),
    }

    # ── Stage 4.5: 渲染（可选） ──
    if not skip_render:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎥 Stage 4.5: Remotion 渲染")
        logger.info("=" * 60)

        try:
            video_path = render_video(
                composition_id="full-video",
                output_path=output_dir / "output.mp4",
                remotion_dir=output_dir,
            )
            result["stages"]["render"] = {
                "video": str(video_path),
            }
        except Exception as e:
            logger.error(f"渲染失败: {e}")
            result["stages"]["render"] = {
                "error": str(e),
            }
    else:
        logger.info("\n⏭️  跳过渲染（使用 --render 启用）")

    # ── 总结 ──
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ Pipeline 完成")
    logger.info("=" * 60)
    logger.info(f"  输出目录: {output_dir}")
    logger.info(f"  场景数量: {len(outline_result.outlines)}")
    logger.info(f"  总时长: {outline_result.total_duration:.0f}s")

    # 保存 pipeline 结果
    result_path = output_dir / "pipeline_result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return result


def main():
    """CLI 入口。"""
    parser = argparse.ArgumentParser(
        description="文/图生视频 Pipeline — 从课程内容生成教学视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python -m pipeline.runner --content "讲解 Python 装饰器" --style styles/tech-dark.json

  # 从文件读取内容
  python -m pipeline.runner --content-file input.md --style styles/apple-keynote.json

  # 启用渲染
  python -m pipeline.runner --content "xxx" --style styles/tech-dark.json --render

  # 指定 LLM
  python -m pipeline.runner --content "xxx" --llm-model gpt-4o --llm-api-key sk-xxx
        """,
    )

    # 输入
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--content", help="课程内容文本")
    input_group.add_argument("--content-file", type=Path, help="课程内容文件")

    # 风格
    parser.add_argument(
        "--style", type=Path,
        default=Path(__file__).resolve().parent.parent / "styles" / "tech-dark.json",
        help="风格配置文件（默认 tech-dark.json）",
    )

    # 视频参数
    parser.add_argument("--duration", type=float, help="目标视频时长（秒）")
    parser.add_argument("--language", default="zh-CN", help="课程语言（默认 zh-CN）")
    parser.add_argument("--render", action="store_true", help="启用 Remotion 渲染")

    # LLM 参数
    parser.add_argument("--llm-model", default="gpt-4o", help="LLM 模型")
    parser.add_argument("--llm-api-key", default="", help="LLM API Key")
    parser.add_argument("--llm-base-url", default="", help="LLM Base URL")

    # TTS 参数
    parser.add_argument("--enable-tts", action="store_true", help="启用 Doubao TTS")
    parser.add_argument("--tts-provider", default="doubao", help="TTS provider（默认 doubao）")
    parser.add_argument(
        "--tts-url",
        default=(
            "http://api-hub.inner.chj.cloud/"
            "bcs-apihub-tools-proxy-service/tool/v1/volcengine/"
            "doubao-llm-speech-synthesis-http"
        ),
        help="Doubao TTS URL",
    )
    parser.add_argument(
        "--tts-gw-token",
        default=os.getenv("X_CHJ_GWTOKEN", "") or os.getenv("JIMENG_SECRET", ""),
        help="Doubao TTS 网关 token（默认读取 X_CHJ_GWTOKEN/JIMENG_SECRET）",
    )
    parser.add_argument(
        "--tts-voice-type",
        default="zh_male_qingcang_mars_bigtts",
        help="Doubao voice_type",
    )
    parser.add_argument(
        "--tts-padding-ms",
        type=int,
        default=300,
        help="TTS 对齐补偿毫秒（默认 300）",
    )

    # 输出
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path.cwd() / "video_output",
        help="输出目录",
    )
    parser.add_argument("--verbose", action="store_true", help="详细日志")

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 读取内容
    if args.content_file:
        content = args.content_file.read_text(encoding="utf-8")
    else:
        content = args.content

    # 加载风格
    style_path = args.style
    if not style_path.is_absolute():
        style_path = Path(__file__).resolve().parent.parent / style_path
    if style_path.exists():
        style = StyleConfig.from_file(style_path)
        logger.info(f"风格: {style.name} ({style_path})")
    else:
        logger.warning(f"风格文件不存在: {style_path}，使用默认风格")
        style = StyleConfig()

    # 构建配置
    config = PipelineConfig(
        style=style,
        output_dir=args.output_dir,
        llm_model=args.llm_model,
        llm_api_key=args.llm_api_key,
        llm_base_url=args.llm_base_url,
        enable_tts=args.enable_tts,
        tts_provider=args.tts_provider,
        tts_url=args.tts_url,
        tts_gw_token=args.tts_gw_token,
        tts_voice_type=args.tts_voice_type,
        tts_padding_ms=args.tts_padding_ms,
        verbose=args.verbose,
    )

    # 执行
    run_pipeline(
        content,
        config,
        target_duration=args.duration,
        language=args.language,
        skip_render=not args.render,
    )


if __name__ == "__main__":
    main()
