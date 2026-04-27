"""
Stage 3: 组装 + 渲染。

功能：
1. 将生成的 SceneCode 写入 .tsx 文件
2. 自动生成 Root.tsx（注册所有 Composition）
3. 自动生成 index.ts（registerRoot 入口）
4. 调用 Remotion CLI 输出 MP4
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import requests

from .types import (
    OutlineResult,
    PipelineConfig,
    SceneCode,
    VideoOutline,
)

logger = logging.getLogger(__name__)

# Remotion 项目模板目录
REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion"
DOUBAO_SUCCESS_CODE = 3000


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


def _sanitize_composition_id(raw_id: str) -> str:
    """将 scene_id 规范化为 Remotion 合法 composition id。"""
    sanitized = raw_id.replace("_", "-")
    sanitized = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff\-]", "-", sanitized)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized or "scene"


def generate_root_tsx(
    scenes: list[SceneCode],
    outlines: list[VideoOutline],
    fps: int = 30,
    scene_audio_map: Optional[dict[str, str]] = None,
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
        composition_id = _sanitize_composition_id(scene.scene_id)

        compositions.append(f"""      <Composition
        id=\"{composition_id}\"
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
    scene_audio_map = scene_audio_map or {}
    for scene in scenes:
        audio_src = scene_audio_map.get(scene.scene_id)
        audio_line = ""
        if audio_src:
            audio_line = f'\n          <Audio src={{staticFile("{audio_src}")}} />'
        sequences.append(f"""        <Sequence from={{{frame_offset}}} durationInFrames={{{scene.duration_frames}}}>
          <{scene.component_name} />{audio_line}
        </Sequence>""")
        frame_offset += scene.duration_frames

    root_code = f'''/**
 * Root.tsx — 自动生成，请勿手动编辑。
 *
 * 由 video_generation pipeline Stage 3 (assembler) 生成。
 * 注册所有场景为独立 Composition，并提供完整视频 Composition。
 */

import {{ Audio, Composition, Sequence, staticFile }} from "remotion";
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


def _build_doubao_tts_headers(gw_token: str) -> dict[str, str]:
    return {
        "BCS-APIHub-RequestId": str(uuid.uuid4()),
        "X-CHJ-GWToken": gw_token,
        "Content-Type": "application/json",
    }


def _synthesize_doubao_tts(
    *,
    text: str,
    tts_url: str,
    tts_gw_token: str,
    voice_type: str,
    speed_ratio: float,
    loudness_ratio: float,
    silence_duration: int,
    timeout: float,
) -> tuple[bytes, int]:
    payload = {
        "app": {"cluster": "volcano_tts"},
        "audio": {
            "context_language": "",
            "encoding": "mp3",
            "explicit_language": "zh",
            "loudness_ratio": loudness_ratio,
            "speed_ratio": speed_ratio,
            "voice_type": voice_type,
        },
        "request": {
            "operation": "query",
            "reqid": str(uuid.uuid4()),
            "silence_duration": silence_duration,
            "text": text,
            "text_type": "plain",
            "with_timestamp": 0,
        },
        "user": {"uid": str(uuid.uuid4())},
    }

    resp = requests.post(
        tts_url,
        headers=_build_doubao_tts_headers(tts_gw_token),
        json=payload,
        timeout=timeout,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f"Doubao TTS HTTP 失败: {exc}; body={resp.text[:1000]}") from exc

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"Doubao TTS 返回非 JSON: {resp.text[:1000]}") from exc

    code = int(data.get("code", -1))
    if code != DOUBAO_SUCCESS_CODE:
        raise RuntimeError(f"Doubao TTS code={code}, body={json.dumps(data, ensure_ascii=False)[:1200]}")

    audio_b64 = str(data.get("data", "")).strip()
    if not audio_b64:
        raise RuntimeError(f"Doubao TTS 缺少 data 字段: {json.dumps(data, ensure_ascii=False)[:1200]}")

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Doubao TTS data base64 解码失败") from exc

    duration_raw = str(data.get("addition", {}).get("duration", "")).strip()
    duration_ms = int(duration_raw) if duration_raw else 0
    return audio_bytes, duration_ms


def synthesize_narration_audio(
    outlines: list[VideoOutline],
    config: PipelineConfig,
    output_dir: Path,
) -> tuple[dict[str, str], dict[str, object]]:
    """
    将每个 scene narration 用 Doubao TTS 合成为 mp3，并保存到 public/audio。

    Returns:
        scene_audio_map: scene_id -> "audio/xxx.mp3"（给 Root.tsx 引用）
        summary: 统计信息
    """
    provider = config.tts_provider.strip().lower()
    if provider not in {"doubao", "volcengine"}:
        raise ValueError(f"暂不支持的 TTS provider: {config.tts_provider}")

    gw_token = config.tts_gw_token.strip() or os.getenv("X_CHJ_GWTOKEN", "").strip() or os.getenv("JIMENG_SECRET", "").strip()
    if not gw_token:
        raise ValueError("缺少 Doubao TTS 网关 token，请传 --tts-gw-token 或设置环境变量 X_CHJ_GWTOKEN/JIMENG_SECRET")

    audio_dir = output_dir / "public" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    scene_audio_map: dict[str, str] = {}
    items: list[dict[str, object]] = []
    total_duration_ms = 0

    for outline in sorted(outlines, key=lambda x: x.order):
        text = (outline.narration or "").strip()
        if not text:
            logger.warning(f"  [TTS] 跳过空旁白: {outline.id}")
            continue

        filename = f"{outline.id}.mp3"
        audio_path = audio_dir / filename
        audio_bytes, duration_ms = _synthesize_doubao_tts(
            text=text,
            tts_url=config.tts_url,
            tts_gw_token=gw_token,
            voice_type=config.tts_voice_type,
            speed_ratio=config.tts_speed_ratio,
            loudness_ratio=config.tts_loudness_ratio,
            silence_duration=config.tts_silence_duration,
            timeout=config.tts_timeout,
        )
        audio_path.write_bytes(audio_bytes)
        scene_audio_map[outline.id] = f"audio/{filename}"
        total_duration_ms += duration_ms
        items.append(
            {
                "scene_id": outline.id,
                "audio_path": str(audio_path),
                "duration_ms": duration_ms,
            }
        )
        logger.info(f"  [TTS] {outline.id}: {audio_path} ({duration_ms}ms)")

    summary = {
        "provider": config.tts_provider,
        "voice_type": config.tts_voice_type,
        "audio_count": len(scene_audio_map),
        "total_duration_ms": total_duration_ms,
        "items": items,
    }

    summary_path = output_dir / "tts_result.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"  TTS 摘要已保存: {summary_path}")
    return scene_audio_map, summary


def generate_entry_ts(
    output_dir: Optional[Path] = None,
) -> Path:
    """生成 Remotion CLI 需要的 registerRoot 入口文件。"""
    target_dir = output_dir or REMOTION_DIR
    entry_path = target_dir / "index.ts"
    entry_code = '''import {registerRoot} from "remotion";
import {RemotionRoot} from "./Root";

registerRoot(RemotionRoot);
'''
    entry_path.write_text(entry_code, encoding="utf-8")
    logger.info(f"  index.ts 已生成: {entry_path}")
    return entry_path


def _resolve_npx_command() -> str:
    """优先使用项目内便携 Node 的 npx，回退系统 npx。"""
    portable_npx = Path(__file__).resolve().parent.parent / ".tools" / "node" / "bin" / "npx"
    if portable_npx.exists():
        return str(portable_npx)
    return "npx"


def render_video(
    composition_id: str = "full-video",
    output_path: Optional[Path] = None,
    remotion_dir: Optional[Path] = None,
    concurrency: int = 2,
) -> Path:
    """
    调用 Remotion CLI 输出 MP4。

    Args:
        composition_id: Composition ID（默认 full-video）
        output_path: 输出文件路径
        remotion_dir: Remotion 项目目录
        concurrency: 并行渲染数

    Returns:
        输出的 MP4 文件路径
    """
    project_dir = (remotion_dir or REMOTION_DIR).resolve()
    output = (output_path or (project_dir / "out" / f"{composition_id}.mp4")).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    entry_path = (project_dir / "index.ts").resolve()
    if not entry_path.exists():
        generate_entry_ts(project_dir)

    npx_cmd = _resolve_npx_command()
    cmd = [
        npx_cmd,
        "--yes",
        "--package=@remotion/cli@4.0.366",
        "remotion",
        "render",
        str(entry_path),
        composition_id,
        str(output),
        "--concurrency",
        str(concurrency),
    ]

    logger.info(f"  渲染: {' '.join(cmd)}")

    env_map = dict(os.environ)
    portable_node_bin = str((Path(__file__).resolve().parent.parent / ".tools" / "node" / "bin").resolve())
    env_map["PATH"] = f"{portable_node_bin}:{env_map.get('PATH', '')}"

    result = subprocess.run(
        cmd,
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        env=env_map,
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
