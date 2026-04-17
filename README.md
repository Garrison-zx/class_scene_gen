# class_scene_gen — 课堂场景生成工具集

本仓库是一套面向教育内容生产的 AI 生成 Pipeline，核心目标是通过 AI 图像生成和视频生成技术，自动批量制作课堂场景图片与场景过渡视频，最终输出可用于在线课程的完整视频素材。

当前课程主题：**向量战法数学课**，以西游记人物（唐僧为老师，孙悟空/猪八戒/沙僧/小白龙为学生）为角色进行课堂还原。

---

## 仓库结构总览

```
class_scene_gen/
├── README.md                    # 本文件
├── image_generation/            # 通用图片生成模块（支持翻译 & 纯生成）
│   ├── image_generation.py      # 主脚本
│   ├── README.md                # 模块专属文档
│   └── prompt/                  # Jinja2 提示词模板
│
├── math_class_gen/              # 数学课堂场景生成主模块
│   ├── math_class_gen_v1.py     # 课堂图生成脚本（当前版本）
│   ├── text2video.py            # 即梦文生视频 API 封装
│   ├── .env                     # 环境配置（API 密钥等，不提交）
│   ├── class_materials/         # 各场景剧本 Markdown 文件
│   ├── generated_images/        # 生成图片输出目录
│   ├── prompt/                  # 课堂场景生成提示词模板
│   ├── style/                   # 参考风格图（style_1-4.png）
│   ├── logs/                    # API 响应历史日志
│   └── temp/                    # 中间产物（座位布局、角色拆解、基准图等）
│
└── video_generation/            # 图生视频模块（即梦 I2V API 封装）
    ├── video_generation.py      # 主脚本
    └── README.md
```

---

## 各模块详细说明

### 1. `image_generation/` — 通用图片生成模块

**定位**：通用工具，支持两类任务：

| 模式 | 说明 | 代表用途 |
|---|---|---|
| 图片→图片 | 输入已有图片，做翻译/风格迁移等处理 | 中文课件图翻译为日文 |
| 纯生成 | 不输入图片，直接由文本描述生成 | 课程封面图生成 |

**核心脚本**：`image_generation.py`

主要功能：
- 通过 Jinja2 模板加载 system/user prompt，注入运行时变量（`{{VAR}}` 或 `${VAR}` 语法）
- 调用 Google Gemini 多模态 API（文本 + 图片输入 → 图片输出）
- 支持单图或批量目录处理，自动注入 `image_name`、`image_stem` 等变量
- 每张图最多重试 5 次，失败输出 `.error.log`，成功输出图片文件 + `.json` 原始响应
- 自动从 `image_generation/.env` 或 `../.env` 加载 `GOOGLE_API_KEY`、`GOOGLE_API_BASE_URL`

**Prompt 命名约定**：
```
prompt/system_<task>.jinja   # 系统提示词
prompt/user_<task>.jinja     # 用户提示词
```

**常用命令**：
```bash
# 图片翻译（中→日）
python3 image_generation/image_generation.py \
  /path/to/input_images \
  --output-dir /path/to/output \
  --prompt-task img_trans_ja

# 封面图纯生成
python3 image_generation/image_generation.py \
  --prompt-task cover_img_gen \
  --output-dir /path/to/output \
  --var COURSE_THEME="工业AI战略与组织转型"
```

---

### 2. `math_class_gen/` — 数学课堂场景生成主模块

这是整个仓库的核心业务模块，包含课堂场景的完整生成链路。

#### 2.1 场景剧本 (`class_materials/`)

共 12 个场景（`scene_01_script.md` ～ `scene_12_script.md`），每个场景的 Markdown 文件描述：

| 部分 | 内容 |
|---|---|
| 人物调度 | 每个角色的位置、手势、台词 |
| 黑板内容 | 本场景的数学题目、板书、标注 |
| 场景定位 | 镜头角度、光线、氛围描述 |
| 课堂剧本 | 该场景的叙事性描述 |

另有 `out_board.md`（黑板清空场景）。

**课程主线**：向量战法数学，从开课到总结共 12 幕，覆盖向量基底、运算方法、例题讲解、互动等环节。

**固定人物设定**：
- 老师：**唐僧**（始终在讲台授课）
- 学生：**孙悟空**（第1排左）、**猪八戒**（第1排右）、**沙僧**（第2排左）、**小白龙**（第2排右）
- 全场座位不可互换（由 `temp/GLOBAL_SEAT_LAYOUT.md` 强制约束）

#### 2.2 图片生成脚本 (`math_class_gen_v1.py`)

**功能**：给定一张基准参考图 + 场景剧本，调用 Gemini 多模态 API 生成对应的课堂场景图。

**工作流程**：
```
基准参考图（base64）+ 场景剧本（Markdown）
        ↓
  system_gen_class_v1.jinja（角色/风格约束）
  user_gen_class_v1.jinja（注入 CLASS_SCRIPT）
        ↓
  Google Gemini API（多模态图片生成）
        ↓
  提取 base64 图片 → 保存 PNG + JSON 响应
```

**运行示例**：
```bash
python3 math_class_gen/math_class_gen_v1.py \
  math_class_gen/style/style_1.png \
  --class-script math_class_gen/class_materials/scene_01_script.md \
  --output-dir math_class_gen/generated_images/
```

#### 2.3 Prompt 模板 (`prompt/`)

| 文件 | 用途 |
|---|---|
| `system_gen_class_v1.jinja` | 系统提示：固定角色、风格、构图规则 |
| `user_gen_class_v1.jinja` | 用户提示：注入 `${CLASS_SCRIPT}` 变量 |
| `system/user_gen_class_background.jinja` | 背景生成任务 |
| `system/user_style_gen.jinja` | 风格生成任务 |

#### 2.4 文生视频脚本 (`text2video.py`)

即梦文生视频 API 的轻量封装，支持从文本 prompt 或 prompt 文件生成视频。目前主要用于测试和早期探索，正式的图生视频方案由 `video_generation/` 模块承担。

#### 2.5 中间产物 (`temp/`)

| 文件 | 说明 |
|---|---|
| `GLOBAL_SEAT_LAYOUT.md` | 全局座位布局约束（所有场景共用） |
| `BASELINE_REFERENCE_IMAGE.json` | 基准参考图的 base64 元数据（~4MB） |
| `scene_XX_board.md` | 各场景黑板内容拆解 |
| `scene_XX_characters.md` | 各场景人物描述拆解 |
| `math_class_gen_temp.py` | 实验性脚本（开发中） |

---

### 3. `video_generation/` — 图生视频模块

**定位**：调用即梦（Jimeng）I2V（Image-to-Video）API，将两张图片（首帧 + 尾帧）合成一段过渡视频。

**核心脚本**：`video_generation.py`

**工作流程**：
```
首帧图片 + 尾帧图片（base64）+ 文本 prompt
        ↓
  即梦 I2V API Submit（提交任务）
        ↓
  轮询 task 状态（默认每 2s 查询一次，最多 120 次）
        ↓
  任务完成 → 下载 MP4 文件
```

**关键参数**：

| 参数 | 说明 |
|---|---|
| `--first-frame` | 首帧图片路径 |
| `--tail-frame` | 尾帧图片路径 |
| `--prompt` | 视频内容描述文本 |
| `--output-dir` | 输出目录 |
| `--task-id` | 已有任务 ID（跳过提交，直接轮询） |
| `--poll-interval` | 轮询间隔（秒，默认 2.0） |
| `--max-polls` | 最大轮询次数（默认 120） |
| `--download` | 自动下载 MP4 |

**环境变量**（`.env`）：

```
JIMENG_I2V_SUBMIT_URL    # 提交任务接口 URL
JIMENG_I2V_RESULT_URL    # 查询结果接口 URL
JIMENG_I2V_REQ_KEY       # 请求密钥
X_CHJ_GWTOKEN            # 网关认证 Token
```

**输出文件**：
```
{task_id}_submit.json       # 提交响应
{task_id}_poll_NNN.json     # 各次轮询响应（可选，需 --save-poll-history）
{task_id}_final.json        # 最终状态
{task_id}.mp4               # 生成视频
```

**注意**：该模块目前处于迭代优化阶段，接口参数和稳定性仍在完善中。

---

## 技术依赖

- Python 3.10+
- `requests`
- `jinja2`（Prompt 模板渲染）
- Google Gemini API（多模态图片生成）
- 即梦（Jimeng）I2V API（图生视频）

---

## 环境配置

在 `math_class_gen/.env` 中配置以下变量：

```env
# Google Gemini（图片生成）
GOOGLE_API_KEY=...
GOOGLE_API_BASE_URL=...

# 即梦 I2V（图生视频）
JIMENG_I2V_SUBMIT_URL=...
JIMENG_I2V_RESULT_URL=...
JIMENG_I2V_REQ_KEY=...
X_CHJ_GWTOKEN=...
```

---

## 下一步计划

> 详见下方"**开发路线图**"

---

# 开发路线图

## 整体 Pipeline 概览

```
math_class_gen/class_materials/          math_class_gen/prompt/
  scene_01_script.md                       system_gen_class_v1.jinja
  scene_02_script.md    ──── Phase 1 ───►  user_gen_class_v1.jinja
  ...                    Gemini I2G API
  scene_12_script.md                           │
                                               ▼
                                    math_class_gen/generated_images/
                                      scene_01.png
                                      scene_02.png  ──── Phase 2 ───►  math_class_gen/generated_videos/
                                      ...             Jimeng I2V API     transition_01_02.mp4
                                      scene_12.png                       transition_02_03.mp4
                                                                         ...
                                                                         transition_11_12.mp4
```

---

## Phase 1：批量课堂场景图片生成

### 目标

遍历 `math_class_gen/class_materials/` 下的 12 个场景剧本，逐个调用 Gemini gemini3-images 图片生成模型，生成对应课堂场景图片，保存到 `math_class_gen/generated_images/`。

### 涉及文件

| 文件 | 角色 |
|---|---|
| `math_class_gen/class_materials/scene_XX_script.md` | 输入：各场景的完整课堂剧本（12个） |
| `math_class_gen/prompt/system_gen_class_v1.jinja` | System Prompt：固定人物、风格、构图约束 |
| `math_class_gen/prompt/user_gen_class_v1.jinja` | User Prompt 模板：注入 `${CLASS_SCRIPT}` 变量 |
| `math_class_gen/generated_images/` | 输出目录：生成的 PNG 图片和原始响应 JSON |
| `image_generation/image_generation.py` | 参考实现：API 调用、图片提取、重试逻辑 |

### Prompt 内容说明

**System Prompt**（`system_gen_class_v1.jinja`，固定不变）：
```
你是专业课堂场景生成AI。
规则：
1. 严格沿用基准图的教室风格、整体布局、人物身份和画风。
2. 人物固定：老师=唐僧，学生=孙悟空、猪八戒、沙僧、小白龙。
3. 唐僧在讲台区域授课，学生坐在座位上面向黑板。
4. 严格按照描述生成动作、表情、黑板内容。
5. 画面清晰、整洁、稳定，不虚化、不变形、不夸张透视。
6. 只输出符合要求的课堂成品图。
```

**User Prompt**（`user_gen_class_v1.jinja`，运行时注入场景剧本）：
```
生成课堂场景：
${CLASS_SCRIPT}
```

其中 `${CLASS_SCRIPT}` 会替换为对应 `scene_XX_script.md` 的完整内容，例如 scene_01 注入后为：
```
生成课堂场景：
### 场景1课堂剧本

#### 人物调度
- 五人同场：唐僧站在讲台后方偏左位置；悟空坐在画面左侧第一排...
#### 黑板内容
- 黑板主标题：`向量斗法课堂：基底法入门`
...
```

### API 调用规格

参考 `image_generation/image_generation.py` 中的 `_ai_call()` 函数，无输入图片（纯文本生成）：

```
POST {GOOGLE_API_BASE_URL}
Headers:
  x-goog-api-key: {GOOGLE_API_KEY}
  Content-Type: application/json

Body:
{
  "systemInstruction": {
    "role": "system",
    "parts": [{"text": "<system_gen_class_v1.jinja 内容>"}]
  },
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "生成课堂场景：\n<scene_XX_script.md 内容>"}]
    }
  ],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"]
  }
}
```

**模型端点**（需在 `.env` 中将 `GOOGLE_API_BASE_URL` 指向图片生成模型）：
```env
# 当前（文本模型，不支持图片输出）：
GOOGLE_API_BASE_URL=.../gemini-3_1-pro-preview:generateContent

# Phase 1 需切换为（gemini3-images，支持图片输出）：
GOOGLE_API_BASE_URL=https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1beta/models/gemini-3-pro-image-preview:generateContent
```

### 响应解析

API 返回 JSON，图片数据在 `candidates[].content.parts[].inlineData` 中：

```json
{
  "candidates": [{
    "content": {
      "parts": [
        {"text": "..."},
        {
          "inlineData": {
            "mimeType": "image/png",
            "data": "<base64 encoded image>"
          }
        }
      ]
    }
  }]
}
```

提取逻辑（参考 `_save_output_images()`）：
1. 遍历 `candidates[].content.parts[]`
2. 找到 `inlineData.mimeType` 以 `image/` 开头的 part
3. `base64.b64decode(inlineData.data)` → 写入 PNG 文件

### 新建脚本：`math_class_gen/batch_image_gen.py`

**输入输出**：
```
输入：math_class_gen/class_materials/scene_01_script.md ... scene_12_script.md
输出：math_class_gen/generated_images/scene_01.png ... scene_12.png
      math_class_gen/generated_images/scene_01.json ... scene_12.json  （原始响应）
      math_class_gen/generated_images/scene_XX.error.log               （失败时）
```

**处理流程**：
```
① 加载 .env（GOOGLE_API_KEY, GOOGLE_API_BASE_URL）
② glob class_materials/scene_*_script.md，按文件名排序
③ 对每个 scene_XX_script.md：
   a. 读取文件内容 → CLASS_SCRIPT
   b. 读取 system_gen_class_v1.jinja → system_prompt
   c. 渲染 user_gen_class_v1.jinja，将 ${CLASS_SCRIPT} 替换 → user_prompt
   d. POST Gemini API（无输入图片）
   e. 从响应 inlineData 提取 base64 → 解码 → 写入 scene_XX.png
   f. 原始响应写入 scene_XX.json
   g. 若失败：等待 5s × attempt 后重试，最多 5 次
   h. 全部重试失败：写入 scene_XX.error.log，继续下一个 scene
④ 打印汇总：成功 N 个，失败 M 个
```

**重试策略**（与 `image_generation.py` 保持一致）：
- 最多重试 5 次
- 第 1 次失败后等待 5s，第 2 次失败后等 10s，第 3 次 15s，以此类推
- 单个 scene 失败不影响其他 scene

**预期运行命令**：
```bash
python3 math_class_gen/batch_image_gen.py \
  --scripts-dir math_class_gen/class_materials \
  --output-dir  math_class_gen/generated_images \
  --prompt-dir  math_class_gen/prompt
```

---

## Phase 2：场景过渡视频生成

### 目标

将 Phase 1 生成的 12 张场景图片，两两配对（scene_i 为首帧，scene_i+1 为尾帧），调用即梦 I2V API 生成 11 段过渡视频，保存到 `math_class_gen/generated_videos/`。

### 涉及文件

| 文件 | 角色 |
|---|---|
| `math_class_gen/generated_images/scene_XX.png` | 输入：Phase 1 生成的场景图片 |
| `math_class_gen/class_materials/scene_XX_script.md` | 输入：提取视频 prompt 文本 |
| `video_generation/video_generation.py` | 参考实现：即梦 I2V 提交、轮询、下载 |
| `math_class_gen/generated_videos/` | 输出目录（**需新建**） |

### 视频帧配对规则

```
首帧（scene_i）       尾帧（scene_i+1）    输出视频
─────────────────────────────────────────────────────
scene_01.png    →    scene_02.png    →    transition_01_02.mp4
scene_02.png    →    scene_03.png    →    transition_02_03.mp4
scene_03.png    →    scene_04.png    →    transition_03_04.mp4
...（共 11 对）
scene_11.png    →    scene_12.png    →    transition_11_12.mp4
```

### 视频 Prompt 生成策略

每段视频的 prompt 从相邻两个场景剧本中提取关键氛围描述，合并后作为视频内容描述。

例如，`transition_01_02.mp4` 的 prompt 可从 scene_01 和 scene_02 的"场景定位"段落中提取：
```
课堂开场，唐僧站在讲台讲解向量基底法，学生们面向黑板坐好，
黑板从标题展示过渡到第一道例题板书。
```

可选方案：
- **自动提取**：解析剧本文件，截取"场景定位"和"课堂剧本"字段拼接
- **手动维护**：新建 `math_class_gen/transition_prompts.json`，为每对场景手写描述

### API 调用规格（基于 `video_generation.py`）

**Step 1：提交生成任务**

```
POST http://api-hub.inner.chj.cloud/bcs-apihub-tools-proxy-service/tool/v1/supplier/volcengine/jimeng-i2v-first-tail-v30
Headers:
  BCS-APIHub-RequestId: <随机 UUID>
  X-CHJ-GWToken: {X_CHJ_GWTOKEN}
  Content-Type: application/json

Body:
{
  "req_key": "jimeng_i2v_first_tail_v30",
  "binary_data_base64": [
    "<scene_i.png 的 base64>",
    "<scene_i+1.png 的 base64>"
  ],
  "prompt": "<从场景剧本提取的过渡描述>"
}

成功响应：
{
  "data": {
    "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

**Step 2：轮询任务状态**

```
POST http://api-hub.inner.chj.cloud/bcs-apihub-tools-proxy-service/tool/v1/supplier/volcengine/jimeng-i2v-first-tail-v30-result
Headers: （同上）

Body:
{
  "req_key": "jimeng_i2v_first_tail_v30",
  "task_id": "<上一步返回的 task_id>"
}

轮询响应：
{
  "data": {
    "status": "processing" | "done" | "failed",
    "video_url": "<视频下载 URL，任务完成后出现>"
  }
}
```

轮询策略：每 2 秒查询一次，最多查询 120 次（约 4 分钟），出现 `video_url` 或 status 为终态则停止。

**Step 3：下载视频**

```python
GET {video_url}  # stream 下载，写入 transition_0i_0j.mp4
```

### `.env` 配置（已就绪）

```env
# 即梦 I2V（图生视频）
X_CHJ_GWTOKEN=eyJ0...   # 已配置，与 JIMENG_SECRET 相同

# 以下字段使用代码内置默认值，无需手动配置：
# JIMENG_I2V_SUBMIT_URL → http://api-hub.inner.chj.cloud/.../jimeng-i2v-first-tail-v30
# JIMENG_I2V_RESULT_URL → http://api-hub.inner.chj.cloud/.../jimeng-i2v-first-tail-v30-result
# JIMENG_I2V_REQ_KEY    → jimeng_i2v_first_tail_v30
```

### 新建脚本：`math_class_gen/batch_video_gen.py`

**输入输出**：
```
输入：math_class_gen/generated_images/scene_01.png ... scene_12.png
      math_class_gen/class_materials/scene_XX_script.md（提取 prompt）
输出：math_class_gen/generated_videos/transition_01_02.mp4
      math_class_gen/generated_videos/transition_02_03.mp4
      ...
      math_class_gen/generated_videos/transition_11_12.mp4
      math_class_gen/generated_videos/transition_0i_0j_submit.json   （提交响应）
      math_class_gen/generated_videos/transition_0i_0j_final.json    （最终响应）
      math_class_gen/generated_videos/transition_0i_0j.error.log     （失败时）
```

**处理流程**：
```
① 加载 .env（X_CHJ_GWTOKEN）
② 确保 generated_videos/ 目录存在，若不存在则创建
③ glob generated_images/scene_*.png，按场景序号排序，得到列表 [s01, s02, ..., s12]
④ 生成配对列表：[(s01,s02), (s02,s03), ..., (s11,s12)]
⑤ 对每对 (scene_i, scene_j)：
   a. 检查 generated_videos/transition_0i_0j.mp4 是否已存在 → 存在则跳过（断点续跑）
   b. 从 scene_i 和 scene_j 对应的剧本文件提取 prompt 文本
   c. 读取 scene_i.png 和 scene_j.png，base64 编码
   d. POST 提交任务 → 获取 task_id
   e. 将提交响应写入 transition_0i_0j_submit.json
   f. 循环轮询（间隔 2s，最多 120 次）：
      - POST 查询 task_id 状态
      - 出现 video_url → 跳出循环
      - status 为 failed/error → 记录失败，跳出
   g. 将最终响应写入 transition_0i_0j_final.json
   h. 下载 video_url 到 transition_0i_0j.mp4
   i. 失败时写入 transition_0i_0j.error.log，继续下一对
⑥ 打印汇总：成功 N 段，失败 M 段
```

**预期运行命令**：
```bash
python3 math_class_gen/batch_video_gen.py \
  --images-dir  math_class_gen/generated_images \
  --scripts-dir math_class_gen/class_materials \
  --output-dir  math_class_gen/generated_videos
```

### `video_generation.py` 已知问题与迭代计划

当前模块基础功能可用，但存在以下问题需在开发 `batch_video_gen.py` 过程中同步修复：

| 问题 | 现状 | 修复方向 |
|---|---|---|
| 错误响应处理不完善 | 非 200 状态码或业务错误码未统一处理 | 解析 `resp.json()` 中的 `code`/`message` 字段，抛出有意义的异常 |
| 状态判断不够健壮 | 仅匹配固定几个 status 字符串 | 扩展 status 映射，增加对 `queued`/`pending` 等中间态的处理 |
| 无超时重试 | 提交失败直接退出 | 参考 `image_generation.py` 加入重试逻辑（最多 3 次，退避等待） |
| 命名不灵活 | `--output-name` 需手动指定 | 在批量脚本中按 `transition_0i_0j.mp4` 规则自动命名 |

---

## 当前进展

| 模块 | 状态 | 说明 |
|---|---|---|
| `image_generation/image_generation.py` | ✅ 可用 | 通用图片生成，支持有/无输入图两种模式 |
| `math_class_gen/math_class_gen_v1.py` | ✅ 可用 | 单场景图片生成，需手动指定单个 scene 文件 |
| `math_class_gen/batch_image_gen.py` | 🔲 待开发 | Phase 1：批量遍历 12 个 scene，自动生成所有图片 |
| `video_generation/video_generation.py` | ⚠️ 基础可用 | 单次 I2V 调用可用，错误处理和重试仍需完善 |
| `math_class_gen/batch_video_gen.py` | 🔲 待开发 | Phase 2：批量生成 11 段过渡视频 |
| `math_class_gen/generated_videos/` | 🔲 待创建 | Phase 2 视频输出目录 |
