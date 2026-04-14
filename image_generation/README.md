# Image Generation Module

## 概述

该目录提供统一的图片生成入口脚本，支持两类任务：

- 图片到图片（有输入图）
- 纯生成任务（无输入图，例如封面图）

主脚本：

- `image_generation.py`

Prompt 目录：

- `prompt/`

## 运行入口

在仓库根目录执行：

```bash
python3 image_generation/image_generation.py [image_dir] [options]
```

- `image_dir` 是可选位置参数。
- 不传 `image_dir` 时，脚本自动进入无输入图模式。

## Prompt 命名规则

通过 `--prompt-task` 选择任务，脚本会按以下规则加载模板：

- `default`
  - `prompt/system_prompt.jinja`
  - `prompt/user_prompt.jinja`
- 其他任务名（示例：`img_trans_ja`）
  - `prompt/system_img_trans_ja.jinja`
  - `prompt/user_img_trans_ja.jinja`
- 兼容：若 `system_<task>.jinja` 不存在，会尝试 `system_<task>.jinja.jinja`

## 模板变量注入

支持两种占位格式（可混用）：

- `{{VAR_NAME}}`
- `${VAR_NAME}`

变量来源：

- `--var KEY=VALUE`（可重复传入）
- `--vars-json '{"K":"V"}'` 或 `--vars-json /path/to/vars.json`

合并优先级：

1. `--vars-json`
2. `--var`（同名覆盖）

逐图处理时，脚本会自动注入：

- `image_name`
- `image_stem`
- `image_ext`
- `image_path`

## 常用命令

### 1) 图片翻译（有输入图）

```bash
python3 image_generation/image_generation.py \
  "/path/to/input_images" \
  --output-dir "/path/to/output_images" \
  --prompt-task img_trans_ja
```

### 2) 纯生成（不传 image_dir，自动无输入图模式）

```bash
python3 image_generation/image_generation.py \
  --prompt-task cover_img_gen \
  --output-dir "/path/to/output" \
  --var COURSE_THEME="工业AI战略与组织转型"
```

### 3) 指定无输入图文件名前缀

```bash
python3 image_generation/image_generation.py \
  --prompt-task cover_img_gen \
  --output-dir "/path/to/output" \
  --no-input-stem "cover_v1"
```

### 4) 目录无图片但仍执行（显式开启）

```bash
python3 image_generation/image_generation.py \
  "/path/to/workdir" \
  --prompt-task cover_img_gen \
  --allow-no-input \
  --output-dir "/path/to/output"
```

### 5) 批量变量注入

```bash
python3 image_generation/image_generation.py \
  --prompt-task cover_img_gen \
  --output-dir "/path/to/output" \
  --vars-json '{"COURSE_THEME":"工业AI战略与组织转型","STYLE":"科幻工业"}'
```

## 输出说明

成功时输出：

- 图片文件：`<stem>.png/.jpg/...`
- 原始响应：`<stem>.json`

失败时输出：

- 错误日志：`<stem>.error.log`

无输入图模式默认 `stem` 为 `generated_cover`，可用 `--no-input-stem` 修改。

## 环境变量

必需：

- `GOOGLE_API_KEY`
- `GOOGLE_API_BASE_URL`

脚本会按顺序加载 `.env`（仅在对应变量未设置时补充）：

1. `image_generation/.env`
2. `image_generation/../.env`

也可直接用系统环境变量覆盖。

## 依赖

- Python 3.10+
- `requests`
