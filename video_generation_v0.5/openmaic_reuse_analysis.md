# OpenMAIC 在文/图生视频中的复用分析

> 目标：将 OpenMAIC 开源项目的六阶段 Pipeline 架构，应用到课堂场景文/图生视频任务中。

---

## 一、OpenMAIC 六阶段 Pipeline 回顾

| Stage | 名称 | 功能 | 可复用程度 |
|-------|------|------|-----------|
| 1 | **大纲生成** | 根据课程主题生成教学大纲 | ⭐⭐⭐⭐⭐ 直接复用 |
| 2 | **场景内容生成** | 为每个大纲条目生成具体场景描述 | ⭐⭐⭐⭐⭐ 直接复用 |
| 3 | **教学动作规划** | 将场景描述转化为具体的教学动作序列 | ⭐⭐⭐⭐ 可复用 |
| 4 | **媒体生成** | 图片/视频生成（5 图片 Provider + 6 视频 Provider） | ⭐⭐⭐ 需适配 |
| 5 | **TTS/Agent** | 文本转语音 + 教学 Agent 交互 | ⭐⭐⭐ 需适配 |
| 6 | **导出回放** | 最终视频导出与回放 | ⭐⭐⭐⭐ 可复用 |

## 二、复用策略：分层对接

### 2.1 上层复用（Stage 1-3：内容规划层）

OpenMAIC 的大纲 → 场景 → 动作 Pipeline 可以直接复用：

```
课程主题
  → [Stage 1] 大纲生成 → 章节/课时列表
  → [Stage 2] 场景内容 → 每个课时的场景描述
  → [Stage 3] 教学动作 → 具体的动作序列（写字、演示、互动等）
```

**具体复用方式：**
- 复用 OpenMAIC 的 prompt 模板体系
- 复用其场景描述格式和变量注入机制
- 直接对接即梦 API 作为 Stage 4 的视频 Provider

### 2.2 中层替换（Stage 4：媒体生成层）

OpenMAIC Stage 4 集成了多种 Provider：

```
图片 Provider: Replicate, DALL·E, SD, Midjourney, ...
视频 Provider: Runway, Pika, Stable Video, ...
```

**替换方案：接入即梦作为核心视频 Provider**

```python
class JimengVideoProvider(BaseVideoProvider):
    """即梦图生视频 Provider"""
    
    def generate(self, scene: Scene) -> Video:
        # 1. 调用 image_generation 生成场景图片
        images = self.image_gen.generate(scene.description)
        
        # 2. 调用 video_generation 生成视频
        #    - 首帧模式：仅首帧图片 + prompt
        #    - 首尾帧模式：首帧 + 尾帧 + prompt
        video = self.video_gen.generate(
            first_frame=images[0],
            tail_frame=images[-1],
            prompt=scene.action_description
        )
        return video
```

### 2.3 下层适配（Stage 5-6：输出层）

- **TTS**：OpenMAIC 支持多种 TTS Provider，可直接复用其架构，接入内部 TTS 服务
- **导出回放**：复用 OpenMAIC 的导出格式（MP4 + JSON 回放脚本）

## 三、整体架构设计

```
┌─────────────────────────────────────────────────────┐
│                    课程生成 Pipeline                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │ Stage 1  │ →  │ Stage 2  │ →  │ Stage 3  │        │
│  │ 大纲生成  │    │ 场景内容  │    │ 动作规划  │        │
│  │ (复用)   │    │ (复用)   │    │ (复用)   │        │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘        │
│       │               │               │               │
│       ▼               ▼               ▼               │
│  ┌──────────────────────────────────────────┐        │
│  │              Stage 4: 媒体生成             │        │
│  │  ┌────────────┐      ┌─────────────┐     │        │
│  │  │ 图片生成     │      │  视频生成      │     │        │
│  │  │ image_gen  │ →    │ video_gen   │     │        │
│  │  │ (复用)     │      │ (即梦 Provider)│    │        │
│  │  └────────────┘      └─────────────┘     │        │
│  └──────────────────┬───────────────────────┘        │
│                     │                                │
│       ┌─────────────┴─────────────┐                  │
│       ▼                           ▼                  │
│  ┌──────────┐              ┌──────────┐              │
│  │ Stage 5  │              │ Stage 6  │              │
│  │ TTS      │              │ 导出回放  │              │
│  │ (适配)   │              │ (复用)   │              │
│  └──────────┘              └──────────┘              │
│                                                       │
└─────────────────────────────────────────────────────┘
```

## 四、代码复用路径

### 4.1 可直接复用的模块

| 模块 | 来源 | 复用方式 |
|------|------|---------|
| 大纲生成 prompt 模板 | OpenMAIC | 直接引用 |
| 场景内容生成 prompt | OpenMAIC | 适配为课堂场景 |
| 教学动作规划 prompt | OpenMAIC | 增加动作类型 |
| 图片生成模块 | class_scene_gen/image_generation | 已有 |
| 视频生成模块 | class_scene_gen/video_generation | 已有 |
| 导出回放格式 | OpenMAIC | 直接复用 |

### 4.2 需要新建的模块

| 模块 | 说明 | 优先级 |
|------|------|--------|
| `jimeng_provider.py` | 即梦视频 Provider，封装 video_generation.py | P0 |
| `pipeline_orchestrator.py` | Pipeline 编排器，串联 6 个 Stage | P0 |
| `scene_planner.py` | 课堂场景规划器（大纲 → 场景 → 动作） | P1 |
| `prompt_library/` | 课堂场景专用 prompt 模板库 | P1 |
| `video_assembler.py` | 视频拼接器（多片段 + TTS） | P2 |

### 4.3 最小可用 Pipeline（MVP）

第一阶段只需跑通简化版：

```
课程主题 → 大纲(Stage1) → 场景描述(Stage2) → 图片(image_gen) → 视频(video_gen)
```

不急于做 TTS 和完整回放，先验证内容生成质量。

## 五、关键差异与适配点

### 5.1 课堂场景 vs 通用教学视频

| 维度 | OpenMAIC | 我们的场景 |
|------|----------|-----------|
| 视频类型 | 通用教学 | 课堂实景分镜 |
| 图片风格 | 多样化 | 统一课堂风格 |
| 动作序列 | 复杂交互 | 以板书/演示为主 |
| 输出格式 | 完整视频 | 分镜片段 + 拼接 |

### 5.2 即梦 API 的能力边界（待实验验证）

- **视频时长**：即梦 v3.0 首尾帧模式约 3-4 秒
- **分辨率**：待确认
- **Prompt 控制力**：待实验评估
- **多图衔接一致性**：待验证

### 5.3 适配策略

1. **用 prompt 模板约束风格**：确保所有生成图片风格一致
2. **分镜粒度控制**：每个分镜 3-4 秒，用动作描述衔接
3. **后处理拼接**：用 ffmpeg 拼接 + 淡入淡出过渡
4. **TTS 同步**：视频拼接后，按时间戳插入 TTS 音频

## 六、实施计划

### Phase 1：即梦实验（本周）
- [ ] 准备测试素材（课堂图片）
- [ ] 创建 prompt 模板
- [ ] 跑通 5 个实验用例
- [ ] 输出即梦能力评估报告

### Phase 2：Pipeline 原型（下周）
- [ ] 创建 `jimeng_provider.py`
- [ ] 创建 `pipeline_orchestrator.py`（简化版）
- [ ] 跑通 主题 → 大纲 → 场景 → 图片 → 视频 完整链路
- [ ] 输出端到端演示

### Phase 3：完整对接（第 3 周）
- [ ] 对接 Stage 1-3（复用 OpenMAIC prompt 体系）
- [ ] 加入 TTS 同步
- [ ] 视频拼接 + 导出回放
- [ ] 输出完整 Demo 视频

## 七、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 即梦 API token 不可用 | 无法实验 | 申请 token / 用 mock 数据 |
| 视频质量不达标 | 需要换 API | 同时调研可灵等其他 API |
| 分镜衔接不一致 | 视频不连贯 | 用 prompt 模板约束 + 后处理 |
| OpenMAIC 代码复杂度高 | 复用困难 | 先复用 prompt 体系，代码逐步适配 |

## 八、参考资源

- OpenMAIC 代码仓：待确认具体地址
- 即梦 API 文档：内部 API Hub
- waytoagi Wiki：AI 视频生成工作流调研（已完成）
- class_scene_gen 代码仓：`https://github.com/Garrison-zx/class_scene_gen.git`
