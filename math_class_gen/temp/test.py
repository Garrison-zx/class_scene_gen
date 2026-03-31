#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


API_URL = (
    "https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1beta/models/"
    "gemini-3-pro-image-preview:generateContent"
)


def compute_retry_delay(exc: Exception, attempt: int) -> int:
    if isinstance(exc, urllib.error.HTTPError):
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after:
            try:
                return max(1, int(retry_after))
            except ValueError:
                pass
        if exc.code == 429:
            return min(180, 20 * attempt)
    return min(90, 3 * attempt)


def write_manifest(manifest_path: Path, manifest_lines: list[str]) -> None:
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")


def parse_index(index_path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    pattern = re.compile(r"-\s+\d+\.\s+(.+?):\s+`([^`]+)`")
    for line in index_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            image_ref = Path(match.group(2))
            image_name = image_ref.name
            if image_name:
                entries.append((match.group(1), image_name))
    return entries


def build_prompt(title: str, mermaid_source: str) -> str:
    return f"""你是一名顶级企业信息设计师。请将附件中的中文业务图表优化为更适合高管汇报/PPT展示的高清信息图。

目标：
1. 保持原始中文信息含义不变。
2. 把附带的 Mermaid 源代码视为权威内容来源，不要改写术语，不要增删关键结论。
3. 允许做更清晰的排版整理，以及允许视觉上的美化，可不完全按照流程图的样式优化，表达含义不变即可。
4. 输出为要复合文本内容风格，突出层次感、对齐、留白、可读性和演示感。
5. 所有中文文字必须逐字逐句与 Mermaid 源代码一致，禁止同音字替换、近形字替换、繁简体误替换、漏字、多字、改写或意译。
6. 如果你无法确认某段中文字符，请保留原图对应位置的中文文本样式，不要自行重写该段文字。

视觉要求：
- 主色调：蓝绿色与深蓝，专业稳重。
- 辅助色：浅黄用于中性阶段，浅粉或红色仅用于风险、瓶颈、失败或警示。
- 中文字体观感：简介现代、适合商业汇报。
- 连接关系：清晰、整洁、尽量减少视觉噪音。
- 可适度美化图表、流程、排版，可加一些背景装饰元素等，保证信息完整、逻辑清晰，不影响教学内容理解

版式要求：
- 文本框不要过于密集，适当增加留白。
- 文字使用方正正粗体保证文本清晰。
- 文本框要与文本内容大小适配，不要过度留白，且文本框中不可以出现文字以外的元素。
- 如果原图是横向流程，继续采用横向布局。
- 如果原图是纵向步骤/大图，继续采用纵向布局。
- 保证中文可读，避免文字过小或相互遮挡。
- 不要书法风、手写风或艺术字效果。



图表标题占位（不可以出现在图片上）：{title}

权威 Mermaid 源代码：
```mermaid
{mermaid_source}
```"""


def request_image(
    api_key: str,
    prompt: str,
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> tuple[bytes, str]:
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read().decode("utf-8"))

    parts = body["candidates"][0]["content"]["parts"]
    text_parts: list[str] = []
    image_part = None
    for part in parts:
        if "text" in part:
            text_parts.append(part["text"])
        if "inlineData" in part:
            image_part = part["inlineData"]

    if not image_part:
        raise RuntimeError("Model returned no image output.")

    image_data = base64.b64decode(image_part["data"])
    response_text = "\n\n".join(text_parts).strip()
    return image_data, response_text


def optimize_entry(
    api_key: str,
    render_root: Path,
    title: str,
    image_name: str,
    out_dir: Path,
) -> tuple[Path, Path]:
    image_path = render_root / "images" / image_name
    source_path = render_root / "mermaid-src" / image_name.replace(".png", ".mmd")

    if not image_path.exists():
        raise FileNotFoundError(f"Missing image: {image_path}")
    if not source_path.exists():
        raise FileNotFoundError(f"Missing Mermaid source: {source_path}")

    prompt = build_prompt(title, source_path.read_text(encoding="utf-8"))
    image_bytes, response_text = request_image(api_key, prompt, image_path.read_bytes())

    out_dir.mkdir(parents=True, exist_ok=True)
    notes_dir = out_dir / "_notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    out_image_path = out_dir / image_name
    out_notes_path = notes_dir / image_name.replace(".png", ".txt")
    out_image_path.write_bytes(image_bytes)
    out_notes_path.write_text(response_text + "\n", encoding="utf-8")
    return out_image_path, out_notes_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_dir", type=Path, help="Project base directory")
    parser.add_argument(
        "--render-root",
        type=Path,
        default=None,
        help="Directory containing index.md, images/, and mermaid-src/",
    )
    parser.add_argument("--limit", type=int, default=0, help="Only optimize first N charts")
    parser.add_argument(
        "--attempts",
        type=int,
        default=6,
        help="Maximum attempts per chart",
    )
    parser.add_argument(
        "--pause-sec",
        type=int,
        default=15,
        help="Pause between successful chart requests",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip output files that already exist",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_GATEWAY_KEY")
    if not api_key:
        print("GEMINI_GATEWAY_KEY is required.", file=sys.stderr)
        return 1

    base_dir = args.base_dir.resolve()
    if args.render_root:
        render_root = args.render_root.resolve()
    elif (base_dir / "output" / "index.md").exists():
        render_root = base_dir / "output"
    elif (base_dir / "index.md").exists():
        render_root = base_dir
    else:
        print(
            "Could not find render output. Pass --render-root or ensure output/index.md exists.",
            file=sys.stderr,
        )
        return 1

    index_path = render_root / "index.md"
    out_dir = render_root / "images-gemini-optimized"
    manifest_path = render_root / "images-gemini-optimized-index.md"

    entries = parse_index(index_path)
    if args.limit > 0:
        entries = entries[: args.limit]

    manifest_lines = ["# Gemini 优化版图表", ""]

    for index, (title, image_name) in enumerate(entries, start=1):
        print(f"[{index}/{len(entries)}] Optimizing {image_name} ...", flush=True)
        out_image_path = out_dir / image_name
        out_notes_path = out_dir / "_notes" / image_name.replace(".png", ".txt")
        if args.skip_existing and out_image_path.exists() and out_notes_path.exists():
            print("  skipped, already exists", flush=True)
            manifest_lines.append(
                f"- {index:02d}. {title}: `images-gemini-optimized/{out_image_path.name}`"
            )
            manifest_lines.append(
                f"  notes: `images-gemini-optimized/_notes/{out_notes_path.name}`"
            )
            write_manifest(manifest_path, manifest_lines)
            continue
        for attempt in range(1, args.attempts + 1):
            try:
                out_image_path, out_notes_path = optimize_entry(
                    api_key=api_key,
                    render_root=render_root,
                    title=title,
                    image_name=image_name,
                    out_dir=out_dir,
                )
                manifest_lines.append(
                    f"- {index:02d}. {title}: `images-gemini-optimized/{out_image_path.name}`"
                )
                manifest_lines.append(
                    f"  notes: `images-gemini-optimized/_notes/{out_notes_path.name}`"
                )
                write_manifest(manifest_path, manifest_lines)
                if index < len(entries) and args.pause_sec > 0:
                    print(f"  waiting {args.pause_sec}s before next chart", flush=True)
                    time.sleep(args.pause_sec)
                break
            except (
                urllib.error.HTTPError,
                urllib.error.URLError,
                RuntimeError,
                TimeoutError,
            ) as exc:
                if attempt == args.attempts:
                    raise
                delay = compute_retry_delay(exc, attempt)
                print(f"  attempt {attempt} failed: {exc}; retrying in {delay}s", flush=True)
                time.sleep(delay)

    write_manifest(manifest_path, manifest_lines)
    print(f"Saved optimized charts to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())