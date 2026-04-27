import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
  Easing,
} from "remotion";

export const Scene08Summary: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // 风格配置
  const colors = {
    background: "#0F1729",
    primary: "#FFFFFF",
    secondary: "#94A3B8",
    accent: "#3B82F6",
    text: "#E2E8F0",
    textSecondary: "#94A3B8",
  };

  const typography = {
    titleFont: "Inter",
    titleSize: 64,
    titleWeight: 700,
    bodyFont: "Inter",
    bodySize: 28,
    bodyWeight: 400,
  };

  const layout = {
    padding: {
      top: 100,
      bottom: 100,
      left: 120,
      right: 120,
    },
  };

  const components = {
    bullet: {
      iconColor: "#3B82F6",
      iconSize: 24,
      spacing: 24,
    },
    progressBar: {
      color: "#3B82F6",
      height: 3,
      background: "rgba(255,255,255,0.1)",
    },
  };

  // 动画计算
  const enterDuration = 20;
  const stagger = 6;

  // 标题动画
  const titleOpacity = interpolate(frame, [0, enterDuration], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, enterDuration], [-50, 0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // 核心要点
  const points = ["打破人力瓶颈", "AI承接专家判断", "规模化复制能力"];

  // 图表动画时间轴
  const diagramStart = 40;
  const morphStart = 100;
  const morphEnd = 130;
  const replicateStart = 160;
  const replicateEnd = 200;

  // 大脑图标动画
  const brainOpacity = interpolate(
    frame,
    [diagramStart, diagramStart + 20, morphStart, morphEnd],
    [0, 1, 1, 0],
    { extrapolateRight: "clamp" }
  );
  const brainScale = spring({
    frame: Math.max(0, frame - diagramStart),
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  // AI芯片动画
  const chipOpacity = interpolate(frame, [morphStart, morphEnd], [0, 1], {
    extrapolateRight: "clamp",
  });
  const chipScale = spring({
    frame: Math.max(0, frame - morphStart),
    fps,
    config: { damping: 12, stiffness: 150 },
  });

  // 芯片复制动画 (向两侧平滑展开)
  const repProgress1 = interpolate(
    frame,
    [replicateStart, replicateEnd],
    [0, 1],
    { extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) }
  );
  const repProgress2 = interpolate(
    frame,
    [replicateStart + 15, replicateEnd + 15],
    [0, 1],
    { extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) }
  );

  const chipOffset1 = repProgress1 * 220;
  const chipOffset2 = repProgress2 * 440;

  const repOpacity1 = interpolate(
    frame,
    [replicateStart, replicateStart + 20],
    [0, 0.6],
    { extrapolateRight: "clamp" }
  );
  const repOpacity2 = interpolate(
    frame,
    [replicateStart + 15, replicateStart + 35],
    [0, 0.3],
    { extrapolateRight: "clamp" }
  );

  // 悬念文字动画
  const suspenseStart = 280;
  const suspenseOpacity = interpolate(
    frame,
    [suspenseStart, suspenseStart + 30],
    [0, 1],
    { extrapolateRight: "clamp" }
  );
  const suspenseY = interpolate(
    frame,
    [suspenseStart, suspenseStart + 30],
    [30, 0],
    { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }
  );

  // 进度条
  const progressWidth = interpolate(frame, [0, durationInFrames], [0, 1920], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: colors.background }}>
      <div
        style={{
          position: "absolute",
          top: layout.padding.top,
          left: layout.padding.left,
          right: layout.padding.right,
          bottom: layout.padding.bottom,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* 标题 */}
        <div
          style={{
            opacity: titleOpacity,
            transform: `translateY(${titleY}px)`,
            marginBottom: 80,
          }}
        >
          <h1
            style={{
              fontFamily: typography.titleFont,
              fontSize: typography.titleSize,
              fontWeight: typography.titleWeight,
              color: colors.primary,
              margin: 0,
              lineHeight: 1.2,
            }}
          >
            破局之路：规模化复制专家能力
          </h1>
        </div>

        {/* 内容区 */}
        <div
          style={{
            display: "flex",
            flex: 1,
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          {/* 左侧：要点列表 */}
          <div
            style={{
              flex: "0 0 45%",
              display: "flex",
              flexDirection: "column",
              gap: 40,
            }}
          >
            {points.map((point, i) => {
              const delay = 20 + i * stagger;
              const itemOpacity = interpolate(
                frame,
                [delay, delay + enterDuration],
                [0, 1],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
              );
              const itemX = interpolate(
                frame,
                [delay, delay + enterDuration],
                [-50, 0],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.out(Easing.cubic),
                }
              );

              return (
                <div
                  key={i}
                  style={{
                    opacity: itemOpacity,
                    transform: `translateX(${itemX}px)`,
                    display: "flex",
                    alignItems: "center",
                    gap: components.bullet.spacing,
                  }}
                >
                  <svg
                    width={components.bullet.iconSize}
                    height={components.bullet.iconSize}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke={components.bullet.iconColor}
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                  <span
                    style={{
                      fontFamily: typography.bodyFont,
                      fontSize: 36,
                      fontWeight: typography.bodyWeight,
                      color: colors.text,
                    }}
                  >
                    {point}
                  </span>
                </div>
              );
            })}
          </div>

          {/* 右侧：示意图区域 */}
          <div
            style={{
              flex: 1,
              position: "relative",
              height: "100%",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            {/* 大脑图标 */}
            <div
              style={{
                position: "absolute",
                opacity: brainOpacity,
                transform: `scale(${brainScale})`,
              }}
            >
              <svg
                width="240"
                height="240"
                viewBox="0 0 24 24"
                fill="none"
                stroke={colors.secondary}
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M9.5 2h5M12 2v2M8.5 6A4.5 4.5 0 0 0 4 10.5c0 1.5.8 2.8 2 3.5v3.5a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-3.5c1.2-.7 2-2 2-3.5A4.5 4.5 0 0 0 15.5 6M12 6v14M8.5 10h7M8.5 14h7" />
              </svg>
            </div>

            {/* AI芯片图标及分身 */}
            <div
              style={{
                position: "absolute",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              {/* 远左侧分身 */}
              <div
                style={{
                  position: "absolute",
                  opacity: repOpacity2,
                  transform: `translateX(-${chipOffset2}px) scale(${
                    chipScale * 0.7
                  })`,
                }}
              >
                <ChipIcon color={colors.accent} />
              </div>
              {/* 左侧分身 */}
              <div
                style={{
                  position: "absolute",
                  opacity: repOpacity1,
                  transform: `translateX(-${chipOffset1}px) scale(${
                    chipScale * 0.85
                  })`,
                }}
              >
                <ChipIcon color={colors.accent} />
              </div>
              {/* 远右侧分身 */}
              <div
                style={{
                  position: "absolute",
                  opacity: repOpacity2,
                  transform: `translateX(${chipOffset2}px) scale(${
                    chipScale * 0.7
                  })`,
                }}
              >
                <ChipIcon color={colors.accent} />
              </div>
              {/* 右侧分身 */}
              <div
                style={{
                  position: "absolute",
                  opacity: repOpacity1,
                  transform: `translateX(${chipOffset1}px) scale(${
                    chipScale * 0.85
                  })`,
                }}
              >
                <ChipIcon color={colors.accent} />
              </div>
              {/* 中心主芯片 */}
              <div
                style={{
                  position: "absolute",
                  opacity: chipOpacity,
                  transform: `scale(${chipScale})`,
                  filter: `drop-shadow(0 0 30px ${colors.accent}66)`,
                }}
              >
                <ChipIcon color={colors.accent} />
              </div>
            </div>
          </div>
        </div>

        {/* 底部悬念文字 */}
        <div
          style={{
            position: "absolute",
            bottom: layout.padding.bottom,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            opacity: suspenseOpacity,
            transform: `translateY(${suspenseY}px)`,
          }}
        >
          <span
            style={{
              fontFamily: typography.titleFont,
              fontSize: 48,
              fontWeight: 700,
              color: colors.accent,
              letterSpacing: "0.1em",
              textShadow: `0 0 20px ${colors.accent}40`,
            }}
          >
            如何起步？
          </span>
        </div>
      </div>

      {/* 底部进度条 */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          height: components.progressBar.height,
          backgroundColor: components.progressBar.background,
        }}
      >
        <div
          style={{
            height: "100%",
            width: progressWidth,
            backgroundColor: components.progressBar.color,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// 辅助组件：AI芯片图标
const ChipIcon: React.FC<{ color: string }> = ({ color }) => (
  <svg
    width="240"
    height="240"
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
    <rect x="9" y="9" width="6" height="6" />
    <line x1="9" y1="1" x2="9" y2="4" />
    <line x1="15" y1="1" x2="15" y2="4" />
    <line x1="9" y1="20" x2="9" y2="23" />
    <line x1="15" y1="20" x2="15" y2="23" />
    <line x1="20" y1="9" x2="23" y2="9" />
    <line x1="20" y1="14" x2="23" y2="14" />
    <line x1="1" y1="9" x2="4" y2="9" />
    <line x1="1" y1="14" x2="4" y2="14" />
  </svg>
);