from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

TTS_URL_DEFAULT = (
    "http://api-hub.inner.chj.cloud/"
    "bcs-apihub-tools-proxy-service/tool/v1/volcengine/"
    "doubao-llm-speech-synthesis-http"
)

DEFAULT_VOICE_TYPE = "zh_male_qingcang_mars_bigtts"
DEFAULT_SPEED_RATIO = 1.0
DEFAULT_LOUDNESS_RATIO = 1.0
DEFAULT_SILENCE_DURATION = 10
DEFAULT_TOLERANCE_MS = 250
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_MIN_SPEED_RATIO = 0.3
DEFAULT_MAX_SPEED_RATIO = 10.0
CHARACTER_ORDER = ["唐僧", "孙悟空", "悟空", "猪八戒", "八戒", "沙僧", "小白龙", "白龙马"]
DEFAULT_VOICE_MAP = {
    "唐僧": "zh_male_qingcang_mars_bigtts",
    "孙悟空": "zh_male_yangguangqingnian_mars_bigtts",
    "猪八戒": "zh_male_fanjuanqingnian_mars_bigtts",
    "沙僧": "zh_male_lengkugege_emo_v2_mars_bigtts",
    "小白龙": "zh_male_yangguangqingnian_mars_bigtts",
}
CHARACTER_NORMALIZATION = {
    "悟空": "孙悟空",
    "八戒": "猪八戒",
    "白龙马": "小白龙",
}


def _load_local_env_file() -> None:
    script_dir = Path(__file__).resolve().parent
    env_candidates = [
        script_dir / ".env",
        script_dir.parent / ".env",
        script_dir.parent / "math_class_gen" / ".env",
        script_dir.parent / "math_class_gen" / ".env.example",
    ]

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


def _new_request_id() -> str:
    return str(uuid.uuid4())


def _build_headers(gw_token: str) -> dict[str, str]:
    return {
        "BCS-APIHub-RequestId": _new_request_id(),
        "X-CHJ-GWToken": gw_token,
        "Content-Type": "application/json",
    }


def _normalize_markdown_text(source: str) -> str:
    lines: list[str] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^[-*]\s*", "", line)
        line = line.replace("`", "")
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _extract_markdown_narration(script_text: str) -> str:
    match = re.search(
        r"^####\s*课堂剧本\s*$([\s\S]*?)(?=^####\s+|\Z)",
        script_text,
        flags=re.MULTILINE,
    )
    source = match.group(1).strip() if match else script_text.strip()
    return _normalize_markdown_text(source)


def _extract_dialogue_text(script_text: str) -> str:
    dialogue_matches = re.findall(r"台词：?[\"“](.*?)[\"”]", script_text)
    cleaned = [_normalize_markdown_text(item) for item in dialogue_matches if item.strip()]
    return "\n".join(item for item in cleaned if item)


def _normalize_character_name(name: str) -> str:
    stripped = name.strip()
    return CHARACTER_NORMALIZATION.get(stripped, stripped)


def _infer_speaker_from_context(context: str) -> str:
    sentence_context = re.split(r"[。\n]", context)[-1]
    first_match_name = ""
    first_match_index: Optional[int] = None
    for candidate in CHARACTER_ORDER:
        idx = sentence_context.find(candidate)
        if idx < 0:
            continue
        if first_match_index is None or idx < first_match_index:
            first_match_index = idx
            first_match_name = candidate

    if first_match_name:
        return _normalize_character_name(first_match_name)

    last_match_name = ""
    last_match_index = -1
    for candidate in CHARACTER_ORDER:
        idx = context.rfind(candidate)
        if idx > last_match_index:
            last_match_index = idx
            last_match_name = candidate

    if last_match_name:
        return _normalize_character_name(last_match_name)
    return "旁白"


def _extract_dialogue_items(script_text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for match in re.finditer(r"台词：?[\"“](.*?)[\"”]", script_text):
        raw_text = _normalize_markdown_text(match.group(1))
        if not raw_text:
            continue
        context = script_text[max(0, match.start() - 120):match.start()]
        speaker = _infer_speaker_from_context(context)
        items.append({"speaker": speaker, "text": raw_text})
    return items


def _read_text_for_tts(script_path: Path, text_mode: str) -> str:
    script_text = script_path.read_text(encoding="utf-8")
    if text_mode == "dialogue":
        text = _extract_dialogue_text(script_text)
    elif text_mode == "classroom":
        text = _extract_markdown_narration(script_text)
    else:
        text = _normalize_markdown_text(script_text)

    if not text:
        raise ValueError(f"脚本中未提取到可配音文本: {script_path}")
    return text


def _parse_voice_map_json(raw: str, fallback_voice_type: str) -> dict[str, str]:
    result = dict(DEFAULT_VOICE_MAP)
    if raw.strip():
        payload = Path(raw).expanduser()
        content = payload.read_text(encoding="utf-8") if payload.exists() and payload.is_file() else raw
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("--voice-map-json 必须是 JSON 对象")
        for key, value in data.items():
            result[_normalize_character_name(str(key))] = str(value)

    for canonical_name in ["唐僧", "孙悟空", "猪八戒", "沙僧", "小白龙", "旁白"]:
        result.setdefault(canonical_name, fallback_voice_type)
    return result


def _offset_timestamps(timestamps: Any, offset_ms: int) -> Any:
    if not isinstance(timestamps, dict):
        return timestamps
    words = timestamps.get("words")
    if not isinstance(words, list):
        return timestamps

    adjusted_words = []
    for word in words:
        if not isinstance(word, dict):
            adjusted_words.append(word)
            continue
        adjusted_word = dict(word)
        if "start_time" in adjusted_word:
            adjusted_word["start_time"] = int(adjusted_word["start_time"]) + offset_ms
        if "end_time" in adjusted_word:
            adjusted_word["end_time"] = int(adjusted_word["end_time"]) + offset_ms
        adjusted_words.append(adjusted_word)

    adjusted = dict(timestamps)
    adjusted["words"] = adjusted_words
    return adjusted


def _concat_audio_files(audio_paths: list[Path], output_path: Path) -> None:
    if not audio_paths:
        raise ValueError("没有可拼接的音频片段")

    if shutil.which("swift") is None:
        with output_path.open("wb") as out_file:
            for audio_path in audio_paths:
                out_file.write(audio_path.read_bytes())
        return

    script_path = Path(__file__).resolve().parent / "merge_audio_segments.swift"
    cmd = ["swift", str(script_path), "--output", str(output_path), "--replace"]
    for audio_path in audio_paths:
        cmd.extend(["--input", str(audio_path)])
    subprocess.run(cmd, check=True)


def _read_uint32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def _read_uint64(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 8], "big")


def _read_atom_size_and_type(data: bytes, offset: int) -> tuple[int, str, int]:
    size = _read_uint32(data, offset)
    atom_type = data[offset + 4:offset + 8].decode("latin-1")
    header_size = 8

    if size == 1:
        size = _read_uint64(data, offset + 8)
        header_size = 16
    elif size == 0:
        size = len(data) - offset

    return size, atom_type, header_size


def _iter_atoms(data: bytes, start: int = 0, end: Optional[int] = None):
    cursor = start
    limit = len(data) if end is None else end

    while cursor + 8 <= limit:
        size, atom_type, header_size = _read_atom_size_and_type(data, cursor)
        if size < header_size:
            break

        atom_end = min(cursor + size, limit)
        yield cursor, atom_end, atom_type, header_size
        cursor += size


def _extract_mvhd_duration_seconds(data: bytes) -> float:
    for moov_start, moov_end, atom_type, header_size in _iter_atoms(data):
        if atom_type != "moov":
            continue

        for child_start, child_end, child_type, child_header_size in _iter_atoms(
            data,
            moov_start + header_size,
            moov_end,
        ):
            if child_type != "mvhd":
                continue

            payload_start = child_start + child_header_size
            version = data[payload_start]
            if version == 1:
                timescale = _read_uint32(data, payload_start + 20)
                duration = _read_uint64(data, payload_start + 24)
            else:
                timescale = _read_uint32(data, payload_start + 12)
                duration = _read_uint32(data, payload_start + 16)

            if timescale <= 0:
                raise ValueError("mvhd timescale 非法")
            return duration / timescale

    raise ValueError("未找到 moov/mvhd，无法解析 MP4 时长")


def _get_video_duration_ms(video_path: Path) -> int:
    data = video_path.read_bytes()
    duration_seconds = _extract_mvhd_duration_seconds(data)
    return round(duration_seconds * 1000)


def _parse_response_duration_ms(resp_json: dict[str, Any]) -> int:
    raw_duration = str(resp_json.get("addition", {}).get("duration", "")).strip()
    if not raw_duration:
        raise ValueError(f"TTS 响应缺少时长字段: {json.dumps(resp_json, ensure_ascii=False)}")
    return int(raw_duration)


def _parse_response_audio_bytes(resp_json: dict[str, Any]) -> bytes:
    raw_audio = str(resp_json.get("data", "")).strip()
    if not raw_audio:
        raise ValueError(f"TTS 响应缺少音频字段: {json.dumps(resp_json, ensure_ascii=False)}")
    return base64.b64decode(raw_audio)


def _extract_timestamps(resp_json: dict[str, Any]) -> Any:
    raw_frontend = resp_json.get("addition", {}).get("frontend")
    if not raw_frontend:
        return {}
    if isinstance(raw_frontend, str):
        try:
            return json.loads(raw_frontend)
        except json.JSONDecodeError:
            return {"raw_frontend": raw_frontend}
    return raw_frontend


def _clamp_speed_ratio(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def synthesize_once(
    *,
    url: str,
    gw_token: str,
    text: str,
    speed_ratio: float,
    voice_type: str,
    loudness_ratio: float,
    silence_duration: int,
    uid: str,
    reqid: str,
    timeout: float,
) -> dict[str, Any]:
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
            "reqid": reqid,
            "silence_duration": silence_duration,
            "text": text,
            "text_type": "plain",
            "with_timestamp": 1,
        },
        "user": {"uid": uid},
    }

    resp = requests.post(
        url,
        headers=_build_headers(gw_token),
        json=payload,
        timeout=timeout,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise requests.HTTPError(f"{exc}; response={resp.text[:1000]}") from exc
    resp_json = resp.json()

    code = int(resp_json.get("code", -1))
    if code != 3000:
        raise ValueError(f"TTS 响应异常: {json.dumps(resp_json, ensure_ascii=False)}")

    return resp_json


def _derive_speed_ratio(
    *,
    current_speed_ratio: float,
    actual_duration_ms: int,
    target_duration_ms: int,
    min_speed_ratio: float,
    max_speed_ratio: float,
) -> float:
    if actual_duration_ms <= 0 or target_duration_ms <= 0:
        return current_speed_ratio

    next_ratio = current_speed_ratio * (actual_duration_ms / target_duration_ms)
    return _clamp_speed_ratio(next_ratio, min_speed_ratio, max_speed_ratio)


def _resolve_transition_pairs(video_dir: Path, script_dir: Path) -> list[tuple[Path, Path, str]]:
    pairs: list[tuple[Path, Path, str]] = []
    for video_path in sorted(video_dir.glob("transition_*.mp4")):
        match = re.fullmatch(r"transition_(\d{2})_(\d{2})\.mp4", video_path.name)
        if not match:
            continue
        target_scene = match.group(2)
        script_path = script_dir / f"scene_{target_scene}_script.md"
        if not script_path.exists():
            raise FileNotFoundError(f"缺少目标脚本: {script_path}")
        pairs.append((video_path, script_path, video_path.stem))
    return pairs


def _resolve_scene_pairs(video_dir: Path, script_dir: Path) -> list[tuple[Path, Path, str]]:
    pairs: list[tuple[Path, Path, str]] = []
    for video_path in sorted(video_dir.glob("scene_*.mp4")):
        match = re.fullmatch(r"(scene_\d{2})[^/]*\.mp4", video_path.name)
        if not match:
            continue
        scene_stem = match.group(1)
        script_path = script_dir / f"{scene_stem}_script.md"
        if not script_path.exists():
            raise FileNotFoundError(f"缺少场景脚本: {script_path}")
        pairs.append((video_path, script_path, video_path.stem))
    return pairs


def _resolve_script_only_pairs(script_dir: Path) -> list[tuple[None, Path, str]]:
    pairs: list[tuple[None, Path, str]] = []
    for script_path in sorted(script_dir.glob("scene_*_script.md")):
        pairs.append((None, script_path, script_path.stem))
    return pairs


def _save_attempt_artifacts(
    *,
    output_dir: Path,
    stem: str,
    attempt: int,
    resp_json: dict[str, Any],
    timestamps: Any,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    attempt_json_path = output_dir / f"{stem}_attempt_{attempt}.json"
    attempt_json_path.write_text(
        json.dumps(resp_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    attempt_timestamp_path = output_dir / f"{stem}_attempt_{attempt}.timestamps.json"
    attempt_timestamp_path.write_text(
        json.dumps(timestamps, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def generate_multivoice_dialogue_audio(
    *,
    script_path: Path,
    output_dir: Path,
    output_stem: str,
    url: str,
    gw_token: str,
    fallback_voice_type: str,
    voice_map: dict[str, str],
    loudness_ratio: float,
    silence_duration: int,
    timeout: float,
) -> None:
    script_text = script_path.read_text(encoding="utf-8")
    dialogue_items = _extract_dialogue_items(script_text)
    if not dialogue_items:
        raise ValueError(f"脚本中未提取到可配音文本: {script_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    segment_audio_paths: list[Path] = []
    combined_words: list[dict[str, Any]] = []
    combined_segments: list[dict[str, Any]] = []
    offset_ms = 0

    for index, item in enumerate(dialogue_items, start=1):
        speaker = _normalize_character_name(item["speaker"])
        text = item["text"]
        voice_type = voice_map.get(speaker, fallback_voice_type)
        reqid = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        try:
            resp_json = synthesize_once(
                url=url,
                gw_token=gw_token,
                text=text,
                speed_ratio=DEFAULT_SPEED_RATIO,
                voice_type=voice_type,
                loudness_ratio=loudness_ratio,
                silence_duration=silence_duration,
                uid=uid,
                reqid=reqid,
                timeout=timeout,
            )
        except Exception:
            if voice_type == fallback_voice_type:
                raise
            print(
                f"{output_stem}: voice_type={voice_type} failed for speaker={speaker}, "
                f"fallback={fallback_voice_type}"
            )
            voice_type = fallback_voice_type
            resp_json = synthesize_once(
                url=url,
                gw_token=gw_token,
                text=text,
                speed_ratio=DEFAULT_SPEED_RATIO,
                voice_type=voice_type,
                loudness_ratio=loudness_ratio,
                silence_duration=silence_duration,
                uid=uid,
                reqid=str(uuid.uuid4()),
                timeout=timeout,
            )

        duration_ms = _parse_response_duration_ms(resp_json)
        audio_bytes = _parse_response_audio_bytes(resp_json)
        timestamps = _extract_timestamps(resp_json)
        adjusted_timestamps = _offset_timestamps(timestamps, offset_ms)

        segment_stem = f"{output_stem}_segment_{index:02d}_{speaker}"
        segment_audio_path = output_dir / f"{segment_stem}.mp3"
        segment_audio_path.write_bytes(audio_bytes)
        segment_audio_paths.append(segment_audio_path)

        _save_attempt_artifacts(
            output_dir=output_dir,
            stem=segment_stem,
            attempt=1,
            resp_json=resp_json,
            timestamps=adjusted_timestamps,
        )

        if isinstance(adjusted_timestamps, dict):
            words = adjusted_timestamps.get("words", [])
            if isinstance(words, list):
                combined_words.extend(words)

        combined_segments.append(
            {
                "speaker": speaker,
                "text": text,
                "voice_type": voice_type,
                "duration_ms": duration_ms,
                "audio_path": str(segment_audio_path),
            }
        )
        offset_ms += duration_ms
        print(
            f"{output_stem}: segment={index} speaker={speaker} "
            f"voice_type={voice_type} audio_ms={duration_ms}"
        )

    final_audio_path = output_dir / f"{output_stem}.m4a"
    _concat_audio_files(segment_audio_paths, final_audio_path)

    final_timestamp_path = output_dir / f"{output_stem}.timestamps.json"
    final_timestamp_path.write_text(
        json.dumps({"words": combined_words}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary_path = output_dir / f"{output_stem}.summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "script_path": str(script_path),
                "text_mode": "dialogue",
                "audio_format": "m4a",
                "audio_duration_ms": offset_ms,
                "segments": combined_segments,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def generate_aligned_audio(
    *,
    video_path: Optional[Path],
    script_path: Path,
    output_dir: Path,
    output_stem: str,
    url: str,
    gw_token: str,
    voice_type: str,
    loudness_ratio: float,
    silence_duration: int,
    text_mode: str,
    start_speed_ratio: float,
    tolerance_ms: int,
    max_attempts: int,
    min_speed_ratio: float,
    max_speed_ratio: float,
    timeout: float,
) -> None:
    text = _read_text_for_tts(script_path, text_mode)
    target_duration_ms = _get_video_duration_ms(video_path) if video_path is not None else 0

    current_speed_ratio = start_speed_ratio
    best_payload: Optional[dict[str, Any]] = None
    best_audio_bytes = b""
    best_timestamps: Any = {}
    best_duration_delta: Optional[int] = None
    best_duration_ms = 0
    best_speed_ratio = current_speed_ratio
    fit_status = "not_started"

    for attempt in range(1, max_attempts + 1):
        reqid = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        resp_json = synthesize_once(
            url=url,
            gw_token=gw_token,
            text=text,
            speed_ratio=current_speed_ratio,
            voice_type=voice_type,
            loudness_ratio=loudness_ratio,
            silence_duration=silence_duration,
            uid=uid,
            reqid=reqid,
            timeout=timeout,
        )

        actual_duration_ms = _parse_response_duration_ms(resp_json)
        audio_bytes = _parse_response_audio_bytes(resp_json)
        timestamps = _extract_timestamps(resp_json)
        duration_delta = abs(actual_duration_ms - target_duration_ms)
        if video_path is None:
            duration_delta = 0

        _save_attempt_artifacts(
            output_dir=output_dir,
            stem=output_stem,
            attempt=attempt,
            resp_json=resp_json,
            timestamps=timestamps,
        )

        if best_duration_delta is None or duration_delta < best_duration_delta:
            best_payload = resp_json
            best_audio_bytes = audio_bytes
            best_timestamps = timestamps
            best_duration_delta = duration_delta
            best_duration_ms = actual_duration_ms
            best_speed_ratio = current_speed_ratio

        print(
            f"{output_stem}: attempt={attempt} "
            f"speed_ratio={current_speed_ratio:.4f} "
            f"audio_ms={actual_duration_ms} "
            f"video_ms={target_duration_ms} "
            f"delta_ms={duration_delta}"
        )

        if video_path is None:
            fit_status = "no_video_alignment"
            break

        if duration_delta <= tolerance_ms:
            fit_status = "within_tolerance"
            break

        next_speed_ratio = _derive_speed_ratio(
            current_speed_ratio=current_speed_ratio,
            actual_duration_ms=actual_duration_ms,
            target_duration_ms=target_duration_ms,
            min_speed_ratio=min_speed_ratio,
            max_speed_ratio=max_speed_ratio,
        )
        if abs(next_speed_ratio - current_speed_ratio) < 1e-4:
            if current_speed_ratio >= max_speed_ratio:
                fit_status = "hit_max_speed_ratio"
            elif current_speed_ratio <= min_speed_ratio:
                fit_status = "hit_min_speed_ratio"
            else:
                fit_status = "stalled"
            break
        current_speed_ratio = next_speed_ratio

    if best_payload is None:
        raise ValueError(f"TTS 生成失败: {output_stem}")

    if fit_status == "not_started":
        fit_status = "best_effort"

    output_dir.mkdir(parents=True, exist_ok=True)

    final_audio_path = output_dir / f"{output_stem}.mp3"
    final_audio_path.write_bytes(best_audio_bytes)

    final_json_path = output_dir / f"{output_stem}.json"
    final_json_path.write_text(
        json.dumps(best_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    final_timestamp_path = output_dir / f"{output_stem}.timestamps.json"
    final_timestamp_path.write_text(
        json.dumps(best_timestamps, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary_path = output_dir / f"{output_stem}.summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "video_path": str(video_path) if video_path is not None else None,
                "script_path": str(script_path),
                "target_duration_ms": target_duration_ms,
                "audio_duration_ms": best_duration_ms,
                "delta_ms": best_duration_delta,
                "voice_type": voice_type,
                "final_speed_ratio": best_speed_ratio,
                "fit_status": fit_status,
                "text_mode": text_mode,
                "text": text,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    _load_local_env_file()

    parser = argparse.ArgumentParser(description="为场景或过渡视频批量生成对齐时长的 TTS 音频")
    parser.add_argument(
        "--mode",
        choices=["transition", "scene", "script"],
        default="script",
        help="transition: transition_01_02.mp4 对应 scene_02_script.md；scene: scene_XX.mp4 对应 scene_XX_script.md；script: 直接按 scene_XX_script.md 生成",
    )
    parser.add_argument(
        "--video-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "math_class_gen" / "generated_videos",
        help="视频目录",
    )
    parser.add_argument(
        "--script-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "math_class_gen" / "class_materials",
        help="场景脚本目录",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "math_class_gen" / "generated_audios",
        help="输出目录",
    )
    parser.add_argument("--tts-url", default=os.getenv("DOUBAO_TTS_HTTP_URL", TTS_URL_DEFAULT))
    parser.add_argument(
        "--gw-token",
        default=_get_env_value("X_CHJ_GWTOKEN", "JIMENG_SECRET", "X-CHJ-GWToken") or "",
        help="网关 token，默认优先读 X_CHJ_GWTOKEN，没有则回退到 JIMENG_SECRET",
    )
    parser.add_argument("--voice-type", default=DEFAULT_VOICE_TYPE)
    parser.add_argument(
        "--voice-map-json",
        default="",
        help="角色到 voice_type 的映射，支持 JSON 字符串或 JSON 文件路径",
    )
    parser.add_argument(
        "--text-mode",
        choices=["dialogue", "classroom", "full"],
        default="dialogue",
        help="dialogue: 只读台词；classroom: 只读课堂剧本段落；full: 读整个 markdown",
    )
    parser.add_argument("--loudness-ratio", type=float, default=DEFAULT_LOUDNESS_RATIO)
    parser.add_argument("--speed-ratio", type=float, default=DEFAULT_SPEED_RATIO)
    parser.add_argument("--silence-duration", type=int, default=DEFAULT_SILENCE_DURATION)
    parser.add_argument("--tolerance-ms", type=int, default=DEFAULT_TOLERANCE_MS)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--min-speed-ratio", type=float, default=DEFAULT_MIN_SPEED_RATIO)
    parser.add_argument("--max-speed-ratio", type=float, default=DEFAULT_MAX_SPEED_RATIO)
    parser.add_argument("--request-timeout", type=float, default=60.0)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="仅处理前 N 条，默认 0 表示全部",
    )
    args = parser.parse_args()

    gw_token = (args.gw_token or "").strip()
    if not gw_token:
        raise ValueError("缺少网关 token，请传 --gw-token 或设置 X_CHJ_GWTOKEN/JIMENG_SECRET")
    voice_map = _parse_voice_map_json(args.voice_map_json, args.voice_type)

    video_dir = args.video_dir.expanduser().resolve()
    script_dir = args.script_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if args.mode == "transition":
        pairs = _resolve_transition_pairs(video_dir, script_dir)
    elif args.mode == "scene":
        pairs = _resolve_scene_pairs(video_dir, script_dir)
    else:
        pairs = _resolve_script_only_pairs(script_dir)

    if not pairs:
        raise FileNotFoundError(f"未找到可处理的输入: {video_dir if args.mode != 'script' else script_dir}")

    if args.limit > 0:
        pairs = pairs[:args.limit]

    for video_path, script_path, output_stem in pairs:
        print(f"processing: {output_stem}")
        try:
            if args.mode == "script" and args.text_mode == "dialogue":
                generate_multivoice_dialogue_audio(
                    script_path=script_path,
                    output_dir=output_dir,
                    output_stem=output_stem,
                    url=args.tts_url,
                    gw_token=gw_token,
                    fallback_voice_type=args.voice_type,
                    voice_map=voice_map,
                    loudness_ratio=args.loudness_ratio,
                    silence_duration=args.silence_duration,
                    timeout=args.request_timeout,
                )
                continue
            generate_aligned_audio(
                video_path=video_path,
                script_path=script_path,
                output_dir=output_dir,
                output_stem=output_stem,
                url=args.tts_url,
                gw_token=gw_token,
                voice_type=args.voice_type,
                loudness_ratio=args.loudness_ratio,
                silence_duration=args.silence_duration,
                text_mode=args.text_mode,
                start_speed_ratio=args.speed_ratio,
                tolerance_ms=args.tolerance_ms,
                max_attempts=args.max_attempts,
                min_speed_ratio=args.min_speed_ratio,
                max_speed_ratio=args.max_speed_ratio,
                timeout=args.request_timeout,
            )
        except ValueError as exc:
            if "未提取到可配音文本" not in str(exc):
                raise

            output_dir.mkdir(parents=True, exist_ok=True)
            skip_path = output_dir / f"{output_stem}.skip.json"
            skip_path.write_text(
                json.dumps(
                    {
                        "script_path": str(script_path),
                        "reason": str(exc),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"{output_stem}: skipped -> {exc}")


if __name__ == "__main__":
    main()
