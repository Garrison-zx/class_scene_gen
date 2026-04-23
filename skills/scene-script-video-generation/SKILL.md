---
name: scene-script-video-generation
description: 基于 class_scene_gen 项目的 Markdown 场景剧本生成课堂场景图、连续场景过渡视频、人物对白配音、带声音的视频片段和最终合成 MP4。适用于用户要求把 scene_XX_script.md 转成图片、图生视频、TTS 对白、多音色配音、音视频合成或完整课程视频的任务。
---

# 场景剧本生成视频

## 概览

在 `class_scene_gen` 中使用这套流程，把 Markdown 场景剧本生成完整课堂视频：

1. 根据每个 `scene_XX_script.md` 生成一张场景图。
2. 用连续两个场景图生成场景过渡视频。
3. 只提取人物明确对白生成 TTS 音频。
4. 将音频合入对应过渡视频；如果音频更长，在结尾帧延长画面。
5. 将所有过渡片段按顺序拼接成一个 MP4。

优先调用仓库里已有脚本，不要重复实现 API 调用逻辑。

## 项目路径

默认仓库根目录是 `/Users/gaozhixing/Desktop/code/openmaic`，除非用户给出其他路径。

核心文件和目录：

- `class_scene_gen/README.md`：模块说明和命令示例。
- `class_scene_gen/image_generation/image_generation.py`：场景图片生成脚本。
- `class_scene_gen/video_generation/video_generation.py`：图生视频过渡片段生成脚本。
- `class_scene_gen/audio_generation/tts_generation.py`：豆包 TTS 配音脚本。
- `class_scene_gen/audio_generation/merge_audio_into_video.swift`：把音频合入视频，必要时延长结尾帧。
- `class_scene_gen/audio_generation/concat_videos.swift`：拼接多个 MP4 片段。
- `class_scene_gen/audio_generation/inspect_media.swift`：检查视频/音频轨道和时长。
- `class_scene_gen/math_class_gen/class_materials/scene_XX_script.md`：场景剧本。
- `class_scene_gen/math_class_gen/class_materials/BASELINE_REFERENCE_IMAGE.png`：图片生成参考图。
- `class_scene_gen/math_class_gen/generated_images`：场景图片输出目录。
- `class_scene_gen/math_class_gen/generated_videos`：过渡视频输出目录。
- `class_scene_gen/math_class_gen/generated_audios_multivoice`：多角色对白音频输出目录。
- `class_scene_gen/math_class_gen/generated_videos_multivoice`：带对白音频的视频片段输出目录。
- `class_scene_gen/math_class_gen/final_videos`：最终合成视频输出目录。

## 环境变量

优先从 `class_scene_gen/math_class_gen/.env` 读取；如果没有 `.env`，可使用 `.env.example`。现有脚本已经实现常见环境文件加载。

需要的变量：

- `GOOGLE_API_KEY`：图片生成。
- `GOOGLE_API_BASE_URL`：可选，Gemini 兼容 API base。
- `JIMENG_I2V_SUBMIT_URL`、`JIMENG_I2V_RESULT_URL`、`JIMENG_I2V_REQ_KEY`、`X_CHJ_GWTOKEN`：即梦图生视频。
- `X_CHJ_GWTOKEN`：同时作为豆包 TTS 网关 token。

运行 Swift 脚本时，通常需要申请文件系统权限，因为 `swift` 会写本地缓存/临时文件。调用网络 API 时，如果沙箱限制网络，也需要申请权限。

## 生成场景图

当用户要求根据场景剧本和基准图生成图片时，使用 `image_generation.py`。

典型输入：

- 参考图：`class_scene_gen/math_class_gen/class_materials/BASELINE_REFERENCE_IMAGE.png`
- 场景剧本：`class_scene_gen/math_class_gen/class_materials/scene_XX_script.md`
- 输出目录：`class_scene_gen/math_class_gen/generated_images`

使用为数学课堂场景配置的 prompt task，例如 `math_class_gen_v1`；具体以 `class_scene_gen/image_generation/prompt/` 中存在的模板为准。

`image_generation.py` 的输出文件名来自输入图片文件名。因此生成单个场景时，要先把基准图复制到临时目录，并命名为目标场景名，例如 `scene_05_script.png`，这样输出才会稳定保存为 `scene_05_script.png`。

单场景生成命令示例：

```bash
cd /Users/gaozhixing/Desktop/code/openmaic

tmp_input_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_input_dir"' EXIT

cp \
  class_scene_gen/math_class_gen/class_materials/BASELINE_REFERENCE_IMAGE.png \
  "$tmp_input_dir/scene_05_script.png"

python3 class_scene_gen/image_generation/image_generation.py \
  "$tmp_input_dir" \
  --prompt-task math_class_gen_v1 \
  --output-dir class_scene_gen/math_class_gen/generated_images \
  --var CLASS_SCRIPT="$(cat class_scene_gen/math_class_gen/class_materials/scene_05_script.md)"
```

批量生成 `scene_05` 到 `scene_12` 的命令示例：

```bash
cd /Users/gaozhixing/Desktop/code/openmaic

tmp_input_dir="$(mktemp -d)"
output_dir="class_scene_gen/math_class_gen/generated_images"
reference_image="class_scene_gen/math_class_gen/class_materials/BASELINE_REFERENCE_IMAGE.png"
script_dir="class_scene_gen/math_class_gen/class_materials"

trap 'rm -rf "$tmp_input_dir"' EXIT
mkdir -p "$output_dir"

for scene in 05 06 07 08 09 10 11 12; do
  rm -f "$tmp_input_dir"/*.png "$tmp_input_dir"/*.jpg "$tmp_input_dir"/*.jpeg "$tmp_input_dir"/*.webp
  cp "$reference_image" "$tmp_input_dir/scene_${scene}_script.png"

  python3 class_scene_gen/image_generation/image_generation.py \
    "$tmp_input_dir" \
    --prompt-task math_class_gen_v1 \
    --output-dir "$output_dir" \
    --var CLASS_SCRIPT="$(cat "$script_dir/scene_${scene}_script.md")"
done
```

如果只生成一个场景，优先使用单场景命令；如果生成多个连续场景，使用批量命令并调整 `for scene in ...` 范围。

如果不确定参数，先查看 `image_generation.py --help` 和现有 prompt 模板。

## 生成过渡视频

为每一组连续场景生成一个过渡视频：

- `scene_01` 图片作为首帧，`scene_02` 图片作为尾帧，使用 `scene_02_script.md` 作为 prompt，输出 `transition_01_02.mp4`。
- 依次生成到 `transition_11_12.mp4`。

使用 `video_generation/video_generation.py`，常用参数包括：

- `--first-frame`
- `--tail-frame`
- `--prompt` 或脚本支持的 prompt 文件参数
- `--output-dir`
- `--download`

过渡视频的 prompt 使用“尾帧/目标场景”的剧本。例如 `transition_04_05` 是从 scene 04 过渡到 scene 05，因此使用 `scene_05_script.md`。

保留 submit/final JSON，便于排查任务失败或下载问题。

## 生成对白配音

默认只给人物对白配音，不生成旁白，除非用户明确要求旁白。`tts_generation.py` 只提取 `台词：“...”` 或 `台词："..."` 这种明确对白；没有对白的场景会跳过。

推荐命令：

```bash
python3 class_scene_gen/audio_generation/tts_generation.py \
  --mode script \
  --text-mode dialogue \
  --script-dir class_scene_gen/math_class_gen/class_materials \
  --output-dir class_scene_gen/math_class_gen/generated_audios_multivoice
```

脚本支持多角色音色，可使用默认角色映射，也可通过 `--voice-map-json` 覆盖。

默认行为：

- 唐僧、孙悟空、猪八戒、沙僧、小白龙分别使用不同 `voice_type`。
- `悟空`、`八戒`、`白龙马` 会归一化为标准角色名。
- 如果某个 `voice_type` 请求失败，会回退到默认音色。

主要输出：

- `scene_XX_script.m4a`：该场景拼接后的对白音频。
- `scene_XX_script.summary.json`：说话人、文本、音色、时长。
- `scene_XX_script.timestamps.json`：合并后的时间戳。
- `scene_XX_script.skip.json`：该场景没有明确对白。

## 合成音视频片段

对有对白音频的场景，将音频合入“以该场景结尾”的过渡视频：

- `scene_02_script.m4a` + `transition_01_02.mp4` -> `scene_02_transition_01_02.mp4`
- `scene_03_script.m4a` + `transition_02_03.mp4` -> `scene_03_transition_02_03.mp4`

命令示例：

```bash
swift class_scene_gen/audio_generation/merge_audio_into_video.swift \
  --video class_scene_gen/math_class_gen/generated_videos/transition_01_02.mp4 \
  --audio class_scene_gen/math_class_gen/generated_audios_multivoice/scene_02_script.m4a \
  --output class_scene_gen/math_class_gen/generated_videos_multivoice/scene_02_transition_01_02.mp4 \
  --replace
```

关键要求：

- 不要截断音频。
- 如果音频比视频长，在视频结尾帧位置延长。
- 不要循环整个视频来补足音频长度，否则会破坏画面连续性。

没有对白的场景，在最终拼接时继续使用原始 `generated_videos/transition_XX_YY.mp4`。

## 拼接最终视频

按顺序构建片段列表，从 `transition_01_02` 到 `transition_11_12`。

每个过渡片段的选择规则：

- 如果存在 `generated_videos_multivoice/scene_YY_transition_XX_YY.mp4`，优先使用它。
- 否则使用 `generated_videos/transition_XX_YY.mp4`。

拼接命令：

```bash
swift class_scene_gen/audio_generation/concat_videos.swift \
  --input <clip-01> \
  --input <clip-02> \
  --input <clip-...> \
  --output class_scene_gen/math_class_gen/final_videos/math_class_full_multivoice.mp4 \
  --replace
```

如果命令很长或不在仓库根目录运行，优先使用绝对路径，减少路径错误。

## 校验结果

检查单个带声音片段和最终 MP4：

```bash
swift class_scene_gen/audio_generation/inspect_media.swift \
  class_scene_gen/math_class_gen/final_videos/math_class_full_multivoice.mp4
```

期望结果：

- `video_tracks=1`
- `audio_tracks=1`
- 音频格式通常是 `aac`
- 最终视频时长应接近所有过渡片段时长之和

如果视频没有声音，先检查：

- 对应场景是否有明确 `台词`。
- 是否生成了 `scene_XX_script.m4a`。
- 最终拼接时是否误用了原始无声 `transition_XX_YY.mp4`，而不是 `generated_videos_multivoice` 里的版本。

## 常见问题

- 不要把视觉描述里的普通引号当作对白；默认只配 `台词`。
- 如果说话人识别不准确，检查 `scene_XX_script.summary.json`，必要时修正剧本文字或角色识别逻辑。
- 不要覆盖用户手动修改过的脚本或生成物，除非用户明确要求重新生成。
- 修改音色映射后，建议使用新输出目录，例如 `generated_audios_multivoice_v2`，避免旧文件混淆。
- 当前环境可能没有 `ffmpeg`，优先使用仓库里的 Swift AVFoundation 辅助脚本。
- 如果某个音色接口返回 403，改用已验证可用的 `mars_bigtts` 音色或回退默认音色。
