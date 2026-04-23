# 文/图生视频 Pipeline

> 从课程内容自动生成教学视频，支持自定义视觉风格。

## 概览

本项目实现了一个三阶段 Pipeline，将课程内容（文本/大纲）转化为可渲染的 Remotion 视频组件：

```
课程内容 + 风格配置
       │
       ▼
┌─────────────────┐
│ Stage 1: 分镜大纲 │  LLM 自动推断场景结构
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ Stage 2: 组件代码生成  │  LLM 生成 Remotion TSX 代码
└────────┬─────────────┘
         │
         ▼
┌────────────────────────┐
│ Stage 3: 组装 + 渲染    │  Root.tsx + npx remotion render → MP4
└────────────────────────┘
```

---

## 目录结构

```
video_generation/
├── README.md                   # 本文档
├── video_generation.py         # 原有的即梦 API 首尾帧图生视频工具
│
├── pipeline/                   # 🔧 Pipeline 核心代码
│   ├── __init__.py
│   ├── types.py                # 类型定义（VideoOutline, SceneCode, StyleConfig 等）
│   ├── outline_generator.py    # Stage 1: 分镜大纲生成
│   ├── scene_generator.py      # Stage 2: Remotion 组件代码生成
│   ├── assembler.py            # Stage 3: 组装 Root.tsx + 渲染
│   └── runner.py               # Pipeline 主入口（CLI）
│
├── prompts/                    # 📝 Prompt 模板
│   ├── 01_scene_outline_system.md   # Stage 1 系统提示词
│   ├── 01_scene_outline_user.md     # Stage 1 用户提示词
│   ├── 02_remotion_scene_system.md  # Stage 2 系统提示词（含风格注入）
│   └── 02_remotion_scene_user.md    # Stage 2 用户提示词
│
├── styles/                     # 🎨 预置风格配置
│   ├── tech-dark.json          # 科技暗色风格
│   ├── apple-keynote.json      # 苹果发布会风格
│   ├── blackboard-chalk.json   # 黑板粉笔风格
│   └── 3b1b-manim.json         # 3Blue1Brown 数学动画风格
│
├── remotion/                   # 🎬 Remotion 项目文件
│   ├── components/             # 公共组件（待实现）
│   └── generated/              # LLM 生成的场景组件（自动生成）
│
├── examples/                   # 📚 示例输入
│   └── python_decorator.md     # 示例：Python 装饰器课程
│
└── tests/                      # 🧪 测试
    └── test_types.py           # 冒烟测试
```

---

## 各模块详解

### 1. pipeline/types.py — 类型定义

定义了 Pipeline 中所有核心数据结构。

#### SceneType（场景类型枚举）

| 类型 | 值 | 说明 |
|------|-----|------|
| TITLE | `title` | 开场标题页，展示课程主题 |
| CONTENT | `content` | 正文内容页，讲解核心知识点 |
| DIAGRAM | `diagram` | 流程图/架构图/关系图 |
| CODE | `code` | 代码演示，逐行高亮讲解 |
| QUIZ | `quiz` | 测验问答 |
| TRANSITION | `transition` | 过渡页，承上启下 |
| SUMMARY | `summary` | 总结页，回顾要点 |

#### VideoOutline（分镜大纲）

Stage 1 的输出，描述单个场景应该展示什么：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | str | 唯一标识，如 `scene_01` |
| `type` | SceneType | 场景类型 |
| `title` | str | 场景标题 |
| `narration` | str | 旁白文本（口语化，供 TTS 使用） |
| `duration_seconds` | float | 场景时长（秒） |
| `order` | int | 排列顺序 |
| `visual_elements` | list[str] | 画面上应出现的视觉元素描述 |
| `animation_hints` | list[str] | 动画效果提示 |
| `key_points` | list[str] | 核心知识点 |
| `code_snippet` | str \| None | 代码片段（type=code 时） |
| `code_language` | str \| None | 代码语言（type=code 时） |

#### StyleConfig（风格配置）

控制视频视觉风格的结构化配置，包含 6 个维度：

| 维度 | 字段 | 说明 |
|------|------|------|
| **画布** | `canvas_width`, `canvas_height`, `fps` | 分辨率和帧率 |
| **配色** | `colors` | background/primary/secondary/accent/text/textSecondary |
| **排版** | `typography` | titleFont/titleSize/bodyFont/bodySize/codeFont |
| **布局** | `layout` | padding/titlePosition/contentAlignment/maxContentWidth |
| **动画** | `animations` | enterType/enterDuration/exitType/stagger/easing |
| **组件** | `components` | codeBlock/bullet/diagram/progressBar 的具体样式 |

加载方式：
```python
from pipeline.types import StyleConfig

# 从文件加载
style = StyleConfig.from_file(Path("styles/apple-keynote.json"))

# 从字典加载
style = StyleConfig.from_json({"name": "custom", "colors": {...}})

# 使用默认值
style = StyleConfig()
```

#### SceneCode（场景代码）

Stage 2 的输出，一个场景对应的 Remotion 组件：

| 字段 | 类型 | 说明 |
|------|------|------|
| `scene_id` | str | 对应 VideoOutline.id |
| `component_name` | str | React 组件名，如 `Scene01Title` |
| `code` | str | 完整的 .tsx 文件内容 |
| `duration_frames` | int | 帧数（= duration_seconds × fps） |

---

### 2. pipeline/outline_generator.py — Stage 1: 分镜大纲生成

**输入**：课程内容文本 + 风格配置
**输出**：`OutlineResult`（包含 `VideoOutline` 列表）

核心流程：
1. 加载 Prompt 模板 `01_scene_outline_system.md`
2. 将风格摘要（配色+画布信息）注入 system prompt
3. 将课程内容注入 user prompt
4. 调用 LLM（OpenAI 兼容接口）
5. 解析 JSON 响应为 `OutlineResult`

```python
from pipeline.outline_generator import generate_outline
from pipeline.types import PipelineConfig, StyleConfig

config = PipelineConfig(
    style=StyleConfig.from_file(Path("styles/tech-dark.json")),
    llm_model="gpt-4o",
    llm_api_key="sk-xxx",
)

result = generate_outline("讲解 Python 装饰器的原理和用法", config)
# result.outlines → [VideoOutline(...), ...]
```

---

### 3. pipeline/scene_generator.py — Stage 2: 组件代码生成

**输入**：`VideoOutline` + `StyleConfig`
**输出**：`SceneCode`（包含 .tsx 组件代码）

核心流程：
1. 加载 Prompt 模板 `02_remotion_scene_system.md`
2. 将**完整的 style.json** 注入 system prompt（这是风格一致性的关键）
3. 将场景大纲信息注入 user prompt
4. 调用 LLM 生成 Remotion React 组件代码
5. 从响应中提取 TSX 代码

**风格注入机制**：
```
System Prompt:
  "你是一个 Remotion 开发者..."
  "## 风格配置（必须严格遵循）"
  "{完整的 style.json 内容}"
  "### 风格遵循规则"
  "1. 所有颜色来自 colors..."
  "2. 字体来自 typography..."
  ...
```

每个场景都注入相同的 style.json，确保所有场景视觉风格一致。

```python
from pipeline.scene_generator import generate_scene_code, generate_all_scenes

# 单个场景
scene = generate_scene_code(outline, config)

# 批量生成
scenes = generate_all_scenes(outline_result.outlines, config)
```

---

### 4. pipeline/assembler.py — Stage 3: 组装 + 渲染

三步操作：

**Step 3.1: 写入 .tsx 文件**
将生成的组件代码保存到 `remotion/generated/` 目录。

**Step 3.2: 生成 Root.tsx**
自动生成 Remotion 入口文件，注册所有场景为独立 Composition + 一个完整视频 Composition。

**Step 3.3: Remotion 渲染（可选）**
调用 `npx remotion render` 输出 MP4。

```python
from pipeline.assembler import write_scene_files, generate_root_tsx, render_video

# 写入文件
paths = write_scene_files(scenes)

# 生成 Root.tsx
root_path = generate_root_tsx(scenes, outlines, fps=30)

# 渲染视频
video_path = render_video(composition_id="full-video")
```

---

### 5. pipeline/runner.py — Pipeline 主入口

串联 Stage 1 → 2 → 3 的 CLI 工具。

```bash
# 基本用法
python -m pipeline.runner \
  --content "讲解 Python 装饰器" \
  --style styles/tech-dark.json

# 从文件读取内容
python -m pipeline.runner \
  --content-file examples/python_decorator.md \
  --style styles/apple-keynote.json

# 指定 LLM 和输出目录
python -m pipeline.runner \
  --content "xxx" \
  --style styles/3b1b-manim.json \
  --llm-model gpt-4o \
  --llm-api-key sk-xxx \
  --output-dir ./my_output

# 启用渲染（需要 Node.js + Remotion 环境）
python -m pipeline.runner \
  --content "xxx" \
  --style styles/tech-dark.json \
  --render
```

CLI 参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--content` | 课程内容文本 | 与 --content-file 二选一 |
| `--content-file` | 课程内容文件 | 与 --content 二选一 |
| `--style` | 风格配置 JSON 文件 | `styles/tech-dark.json` |
| `--duration` | 目标视频时长（秒） | 自动推断 |
| `--language` | 课程语言 | `zh-CN` |
| `--render` | 启用 Remotion 渲染 | 关闭 |
| `--llm-model` | LLM 模型名 | `gpt-4o` |
| `--llm-api-key` | LLM API Key | - |
| `--llm-base-url` | LLM Base URL | - |
| `--output-dir` | 输出目录 | `./video_output` |
| `--verbose` | 详细日志 | 关闭 |

---

### 6. prompts/ — Prompt 模板

参考 OpenMAIC 的 Prompt 工程设计。

#### 01_scene_outline_system.md（Stage 1 系统提示词）

定义了：
- 视频编导角色
- 7 种场景类型的用途和典型时长
- 旁白设计原则（口语化、简洁、信息密度适中）
- 视觉元素设计规范
- 动画提示编写规范
- 风格摘要注入（`{{style_summary}}`）
- JSON 输出格式定义

关键设计：旁白和视觉元素分离，对标 OpenMAIC 的"内容和行为分离"原则。

#### 02_remotion_scene_system.md（Stage 2 系统提示词）

定义了：
- Remotion 开发者角色
- Remotion 核心 API 参考（useCurrentFrame, interpolate, spring, Sequence）
- 常用动画模式代码示例（淡入、滑入、弹性、逐条出现、代码高亮）
- **完整 style.json 注入**（`{{style_config}}`）
- 风格遵循规则（颜色/字体/间距/动画/组件样式）
- 7 种场景类型的特定要求
- 质量检查清单

关键设计：style.json 在这里完整注入，是风格一致性的核心保障。

---

### 7. styles/ — 预置风格配置

4 套开箱即用的风格：

| 文件 | 风格名 | 特点 |
|------|--------|------|
| `tech-dark.json` | Tech Dark | 深蓝背景、蓝色强调、适合技术课程 |
| `apple-keynote.json` | Apple Keynote | 纯黑背景、大字居中、极简动画 |
| `blackboard-chalk.json` | Blackboard Chalk | 深绿黑板、粉笔白字、手写感 |
| `3b1b-manim.json` | 3Blue1Brown | 深色背景、几何配色、数学优雅 |

#### 风格配置字段说明

```json
{
  "name": "风格名称",
  "description": "风格描述",

  "canvas": {
    "width": 1920,        // 画布宽度（px）
    "height": 1080,       // 画布高度（px）
    "fps": 30             // 帧率
  },

  "colors": {
    "background": "#xxx", // 背景色
    "primary": "#xxx",    // 主色调（标题）
    "secondary": "#xxx",  // 次要色
    "accent": "#xxx",     // 强调色（高亮、按钮）
    "text": "#xxx",       // 正文颜色
    "textSecondary": "#xxx" // 次要文字颜色
  },

  "typography": {
    "titleFont": "字体名",    // 标题字体
    "titleSize": 64,          // 标题字号
    "titleWeight": 700,       // 标题字重
    "bodyFont": "字体名",     // 正文字体
    "bodySize": 28,           // 正文字号
    "codeFont": "等宽字体名"   // 代码字体
  },

  "layout": {
    "padding": { "top": 100, "bottom": 100, "left": 120, "right": 120 },
    "titlePosition": "center|top-left|top-center",
    "contentAlignment": "left|center",
    "maxContentWidth": 1400
  },

  "animations": {
    "enterType": "fadeIn|write|handwrite",  // 入场动画类型
    "enterDuration": 20,                     // 入场动画帧数
    "exitType": "fadeOut",                   // 退场动画类型
    "exitDuration": 15,                      // 退场动画帧数
    "stagger": 6,                            // 多元素交错间隔（帧）
    "easing": "easeInOutCubic"               // 缓动函数
  },

  "components": {
    "codeBlock": { ... },     // 代码块样式
    "bullet": { ... },        // 要点列表样式
    "diagram": { ... },       // 图表样式
    "progressBar": { ... }    // 进度条样式
  },

  "transitions": {
    "between_scenes": "crossfade|wipe|fadethrough",
    "duration": 15
  }
}
```

#### 自定义风格

复制任意预置风格文件，修改后保存为新文件：

```bash
cp styles/tech-dark.json styles/my-custom.json
# 编辑 my-custom.json
python -m pipeline.runner --content "xxx" --style styles/my-custom.json
```

---

### 8. 与 OpenMAIC 的对应关系

本方案借鉴了 OpenMAIC 的 Pipeline 架构，但针对视频渲染场景做了关键调整：

| OpenMAIC | 本方案 | 差异说明 |
|----------|--------|---------|
| UserRequirements | 课程内容 + style.json | 增加结构化风格配置 |
| SceneOutline | VideoOutline | 增加 duration、narration、animation_hints |
| 5 种 Widget Prompt | 1 个统一的 remotion-scene Prompt | 简化为一套 Prompt + 风格注入 |
| 自包含 HTML | Remotion .tsx 组件 | 从浏览器交互改为视频渲染 |
| Actions (speech/spotlight) | Remotion Sequence + 时间线 | 从运行时行为改为编译时时间线 |
| 浏览器播放 | npx remotion render -> MP4 | 离线渲染 |
| 无风格系统 | **style.json 风格配置** | 核心创新：风格可控 |

---

### 9. 与已有工具的关系

本模块和 `video_generation.py`（即梦首尾帧图生视频）是互补关系：

| 工具 | 用途 | 输入 | 输出 |
|------|------|------|------|
| `video_generation.py` | 即梦 API 图生视频 | 首帧图片 + 尾帧图片 + prompt | MP4（API 生成） |
| `pipeline/` | LLM 生成教学视频 | 课程文本 + 风格配置 | Remotion 组件 / MP4 |

可以组合使用：Pipeline 生成课程视频的静态帧，再用即梦 API 生成场景间的过渡动画。

---

## 快速开始

### 前置依赖

```bash
# Python 依赖
pip install openai

# Remotion 渲染（可选）
npm install -g @remotion/cli
# 或项目内安装
cd remotion && npm init remotion@latest
```

### 运行测试

```bash
cd video_generation
python tests/test_types.py
```

### 运行 Pipeline（需要 LLM API Key）

```bash
cd video_generation
python -m pipeline.runner \
  --content-file examples/python_decorator.md \
  --style styles/tech-dark.json \
  --llm-api-key sk-xxx \
  --output-dir ./output
```

---

## 下一步

- [ ] 接入具体 LLM API（火山引擎/OpenAI）进行端到端测试
- [ ] 实现 Remotion 公共组件（AnimatedTitle, BulletList, CodeBlock）
- [ ] TTS 旁白生成集成（edge-tts / 火山引擎语音合成）
- [ ] 更多预置风格
- [ ] 效果评估和 Prompt 迭代
