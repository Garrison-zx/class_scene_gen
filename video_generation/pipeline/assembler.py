"""
Stage 3: 组装 + 渲染。

功能：
1. 将生成的 SceneCode 写入 .tsx 文件
2. 自动生成 Root.tsx（注册所有 Composition）
3. 可选：生成旁白音频（TTS）
4. 调用 npx remotion render 输出 MP4
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .types import (
    OutlineResult,
    PipelineConfig,
    SceneCode,
    VideoOutline,
)

logger = logging.getLogger(__name__)

# Remotion 项目模板目录
REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion"


def write_scene_files(
    scenes: list[SceneCode],
    output_dir: Optional[Path] = None,
) -> list[Path]:
    """
    将生成的组件代码写入 .tsx 文件。

    Args:
        scenes: SceneCode 列表
        output_dir: 输出目录，默认为 remotion/generated/

    Returns:
        写入的文件路径列表
    """
    target_dir = output_dir or (REMOTION_DIR / "generated")
    target_dir.mkdir(parents=True, exist_ok=True)

    # 清理旧文件
    for old_file in target_dir.glob("Scene*.tsx"):
        old_file.unlink()

    paths: list[Path] = []
    for scene in scenes:
        filename = f"{scene.component_name}.tsx"
        filepath = target_dir / filename
        filepath.write_text(scene.code, encoding="utf-8")
        paths.append(filepath)
        logger.info(f"  写入: {filepath}")

    return paths


def generate_root_tsx(
    scenes: list[SceneCode],
    outlines: list[VideoOutline],
    fps: int = 30,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    自动生成 Root.tsx，注册所有场景为 Remotion Composition。

    Args:
        scenes: SceneCode 列表
        outlines: VideoOutline 列表（用于获取时长信息）
        fps: 帧率
        output_dir: 输出目录

    Returns:
        Root.tsx 文件路径
    """
    target_dir = output_dir or REMOTION_DIR
    root_path = target_dir / "Root.tsx"

    # 构建 outline 字典方便查询
    outline_map = {o.id: o for o in outlines}

    # import 语句
    imports = []
    compositions = []

    for scene in scenes:
        imports.append(
            f'import {{ {scene.component_name} }} from "./generated/{scene.component_name}";'
        )

        outline = outline_map.get(scene.scene_id)
        title = outline.title if outline else scene.scene_id

        compositions.append(f"""      <Composition
        id="{scene.scene_id}"
        component={{{scene.component_name}}}
        durationInFrames={{{scene.duration_frames}}}
        fps={{{fps}}}
        width={{1920}}
        height={{1080}}
      />""")

    # 完整视频 Composition（所有场景串联）
    total_frames = sum(s.duration_frames for s in scenes)

    sequences = []
    frame_offset = 0
    for scene in scenes:
        sequences.append(f"""        <Sequence from={{{frame_offset}}} durationInFrames={{{scene.duration_frames}}}>
          <{scene.component_name} />
        </Sequence>""")
        frame_offset += scene.duration_frames

    root_code = f'''/**
 * Root.tsx — 自动生成，请勿手动编辑。
 *
 * 由 video_generation pipeline Stage 3 (assembler) 生成。
 * 注册所有场景为独立 Composition，并提供完整视频 Composition。
 */

import {{ Composition, Sequence }} from "remotion";
{chr(10).join(imports)}

export const RemotionRoot: React.FC = () => {{
  return (
    <>
      {{/* ── 独立场景（方便单独预览） ── */}}
{chr(10).join(compositions)}

      {{/* ── 完整视频（所有场景串联） ── */}}
      <Composition
        id="full-video"
        component={{FullVideo}}
        durationInFrames={{{total_frames}}}
        fps={{{fps}}}
        width={{1920}}
        height={{1080}}
      />
    </>
  );
}};

const FullVideo: React.FC = () => {{
  return (
    <>
{chr(10).join(sequences)}
    </>
  );
}};
'''

    root_path.write_text(root_code, encoding="utf-8")
    logger.info(f"  Root.tsx 已生成: {root_path}")
    logger.info(f"  总帧数: {total_frames} ({total_frames / fps:.1f}s @ {fps}fps)")

    return root_path


def render_video(
    composition_id: str = "full-video",
    output_path: Optional[Path] = None,
    remotion_dir: Optional[Path] = None,
    concurrency: int = 2,
) -> Path:
    """
    调用 npx remotion render 输出 MP4。

    Args:
        composition_id: Composition ID（默认 full-video）
        output_path: 输出文件路径
        remotion_dir: Remotion 项目目录
        concurrency: 并行渲染数

    Returns:
        输出的 MP4 文件路径
    """
    project_dir = remotion_dir or REMOTION_DIR
    output = output_path or (project_dir / "out" / f"{composition_id}.mp4")
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "npx", "remotion", "render",
        str(project_dir / "Root.tsx"),
        composition_id,
        str(output),
        "--concurrency", str(concurrency),
    ]

    logger.info(f"  渲染: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"渲染失败:\n{result.stderr}")
        raise RuntimeError(f"Remotion 渲染失败: {result.stderr}")

    logger.info(f"  ✅ 视频输出: {output}")
    return output


def save_outline_json(
    outline_result: OutlineResult,
    output_dir: Path,
) -> Path:
    """保存大纲 JSON（方便调试和复用）。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "outline.json"

    data = {
        "language_directive": outline_result.language_directive,
        "total_duration": outline_result.total_duration,
        "outlines": [
            {
                "id": o.id,
                "type": o.type.value,
                "title": o.title,
                "narration": o.narration,
                "duration_seconds": o.duration_seconds,
                "order": o.order,
                "visual_elements": o.visual_elements,
                "animation_hints": o.animation_hints,
                "key_points": o.key_points,
                "code_snippet": o.code_snippet,
                "code_language": o.code_language,
            }
            for o in outline_result.outlines
        ],
    }

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"  大纲 JSON 已保存: {path}")
    return path
