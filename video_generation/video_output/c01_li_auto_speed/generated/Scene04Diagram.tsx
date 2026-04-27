import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
  interpolateColors,
} from "remotion";

export const Scene04Diagram: React.FC = () => {
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
    warning: "#F59E0B",
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
    diagram: {
      nodeBackground: "#1E293B",
      nodeBorder: "#334155",
      nodeBorderRadius: 12,
      arrowColor: "#94A3B8",
    },
    progressBar: {
      color: "#3B82F6",
      height: 3,
      background: "rgba(255,255,255,0.1)",
    },
  };

  // 动画参数
  const enterDuration = 20;
  const exitDuration = 15;
  const stagger = 6;

  // 全局退场动画
  const globalOpacity = interpolate(
    frame,
    [durationInFrames - exitDuration, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // 标题入场
  const titleOpacity = interpolate(frame, [0, enterDuration], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, enterDuration], [-30, 0], {
    extrapolateRight: "clamp",
  });

  // 布局坐标计算
  const leftNodeX = layout.padding.left;
  const startY = 280;
  const nodeWidth = 260;
  const nodeHeight = 70;
  const nodeSpacing = 100;
  const numDevices = 6;

  const rightNodeX = 1920 - layout.padding.right - 320;
  const rightNodeY = 480;
  const rightNodeWidth = 320;
  const rightNodeHeight = 140;

  // 工程师节点（右侧）动画
  const engineerDelay = 80;
  const engineerOpacity = interpolate(
    frame,
    [engineerDelay, engineerDelay + enterDuration],
    [0, 1],
    { extrapolateRight: "clamp" }
  );
  const engineerScale = spring({
    frame: Math.max(0, frame - engineerDelay),
    fps,
    config: { damping: 15, stiffness: 150 },
  });

  const overloadStart = 140;
  const isOverloaded = frame > overloadStart;
  
  const engineerBg = interpolateColors(
    frame,
    [overloadStart, overloadStart + 30],
    [components.diagram.nodeBackground, "rgba(245, 158, 11, 0.15)"]
  );
  const engineerBorder = interpolateColors(
    frame,
    [overloadStart, overloadStart + 30],
    [components.diagram.nodeBorder, colors.warning]
  );
  const engineerTextColor = interpolateColors(
    frame,
    [overloadStart, overloadStart + 30],
    [colors.text, colors.warning]
  );

  // 震动效果
  const shakeX = isOverloaded ? Math.sin((frame - overloadStart) * 1.5) * 6 : 0;
  const shakeY = isOverloaded ? Math.cos((frame - overloadStart) * 1.8) * 3 : 0;

  // 中间数据点文本动画
  const dataTextDelay = 100;
  const dataTextOpacity = interpolate(
    frame,
    [dataTextDelay, dataTextDelay + enterDuration],
    [0, 1],
    { extrapolateRight: "clamp" }
  );
  const dataTextScale = spring({
    frame: Math.max(0, frame - dataTextDelay),
    fps,
    config: { damping: 12, stiffness: 120 },
  });

  // 进度条计算
  const progressWidth = interpolate(
    frame,
    [0, durationInFrames],
    [0, 1920],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: colors.background, opacity: globalOpacity }}>
      {/* 标题 */}
      <div
        style={{
          position: "absolute",
          top: layout.padding.top,
          left: layout.padding.left,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          fontFamily: typography.titleFont,
          fontSize: typography.titleSize,
          fontWeight: typography.titleWeight,
          color: colors.primary,
        }}
      >
        产线质量管理的困境
      </div>

      {/* 连线与粒子层 (SVG) */}
      <svg
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      >
        {Array.from({ length: numDevices }).map((_, i) => {
          const delay = 20 + i * stagger;
          const lineOpacity = interpolate(
            frame,
            [delay + 20, delay + 40],
            [0, 0.3],
            { extrapolateRight: "clamp" }
          );

          const startPx = leftNodeX + nodeWidth;
          const startPy = startY + i * nodeSpacing + nodeHeight / 2;
          const endPx = rightNodeX + shakeX;
          const endPy = rightNodeY + rightNodeHeight / 2 + shakeY;

          // 贝塞尔曲线控制点，形成漏斗状
          const cp1x = startPx + 300;
          const cp1y = startPy;
          const cp2x = endPx - 300;
          const cp2y = endPy;
          const pathD = `M ${startPx} ${startPy} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${endPx} ${endPy}`;

          // 粒子动画
          const numParticles = 8;
          const particles = Array.from({ length: numParticles }).map((_, pIdx) => {
            const particleFlowStart = delay + 30;
            const isActive = frame > particleFlowStart;
            
            // 粒子进度 0-1
            const speed = 120; // 粒子跑完全程需要的帧数
            const offset = pIdx * (speed / numParticles);
            const rawProgress = (frame - particleFlowStart + offset) % speed;
            const progress = rawProgress / speed;

            // 简单的二次贝塞尔曲线插值计算粒子位置
            const t = progress;
            const u = 1 - t;
            const tt = t * t;
            const uu = u * u;
            const uuu = uu * u;
            const ttt = tt * t;

            const px = uuu * startPx + 3 * uu * t * cp1x + 3 * u * tt * cp2x + ttt * endPx;
            const py = uuu * startPy + 3 * uu * t * cp1y + 3 * u * tt * cp2y + ttt * endPy;

            const pOpacity = isActive && progress > 0.05 && progress < 0.95 ? 1 : 0;
            
            // 粒子颜色：靠近右侧时变为警告色
            const pColor = interpolateColors(
              progress,
              [0, 0.7, 1],
              [colors.accent, colors.accent, colors.warning]
            );

            // 粒子大小：靠近右侧时变大，暗示堆积
            const pRadius = interpolate(progress, [0, 1], [3, 6]);

            return (
              <circle
                key={`p-${i}-${pIdx}`}
                cx={px}
                cy={py}
                r={pRadius}
                fill={pColor}
                opacity={pOpacity}
                style={{ filter: `drop-shadow(0 0 4px ${pColor})` }}
              />
            );
          });

          return (
            <g key={`flow-${i}`}>
              <path
                d={pathD}
                fill="none"
                stroke={components.diagram.arrowColor}
                strokeWidth={2}
                opacity={lineOpacity}
                strokeDasharray="4 4"
              />
              {particles}
            </g>
          );
        })}
      </svg>

      {/* 左侧设备节点 */}
      {Array.from({ length: numDevices }).map((_, i) => {
        const delay = 20 + i * stagger;
        const opacity = interpolate(frame, [delay, delay + enterDuration], [0, 1], {
          extrapolateRight: "clamp",
        });
        const scale = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 15, stiffness: 150 },
        });

        const isLit = frame > delay + 15;
        const borderColor = isLit ? colors.accent : components.diagram.nodeBorder;
        const textColor = isLit ? colors.primary : colors.textSecondary;
        const shadow = isLit ? `0 0 15px rgba(59, 130, 246, 0.3)` : "none";

        const isLast = i === numDevices - 1;
        const label = isLast ? "1500+ 产线设备" : `产线设备 ${String(i + 1).padStart(3, "0")}`;

        return (
          <div
            key={`device-${i}`}
            style={{
              position: "absolute",
              left: leftNodeX,
              top: startY + i * nodeSpacing,
              width: nodeWidth,
              height: nodeHeight,
              backgroundColor: components.diagram.nodeBackground,
              border: `2px solid ${borderColor}`,
              borderRadius: components.diagram.nodeBorderRadius,
              opacity,
              transform: `scale(${scale})`,
              display: "flex",
              alignItems: "center",
              paddingLeft: 24,
              boxShadow: shadow,
              transition: "all 0.3s ease",
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                backgroundColor: isLit ? colors.accent : components.diagram.nodeBorder,
                marginRight: 16,
                boxShadow: isLit ? `0 0 8px ${colors.accent}` : "none",
              }}
            />
            <span
              style={{
                fontFamily: typography.bodyFont,
                fontSize: 22,
                fontWeight: isLast ? 700 : 400,
                color: isLast ? colors.accent : textColor,
              }}
            >
              {label}
            </span>
          </div>
        );
      })}

      {/* 中间数据点文本 */}
      <div
        style={{
          position: "absolute",
          left: 1920 / 2 - 150,
          top: rightNodeY - 120,
          opacity: dataTextOpacity,
          transform: `scale(${dataTextScale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div
          style={{
            fontFamily: typography.titleFont,
            fontSize: 48,
            fontWeight: 700,
            color: colors.primary,
            textShadow: `0 0 20px rgba(255,255,255,0.2)`,
          }}
        >
          50000+
        </div>
        <div
          style={{
            fontFamily: typography.bodyFont,
            fontSize: 24,
            color: colors.accent,
            marginTop: 8,
            backgroundColor: "rgba(59, 130, 246, 0.1)",
            padding: "4px 16px",
            borderRadius: 20,
            border: `1px solid rgba(59, 130, 246, 0.3)`,
          }}
        >
          实时工艺数据点
        </div>
      </div>

      {/* 右侧工程师节点（瓶颈） */}
      <div
        style={{
          position: "absolute",
          left: rightNodeX + shakeX,
          top: rightNodeY + shakeY,
          width: rightNodeWidth,
          height: rightNodeHeight,
          backgroundColor: engineerBg,
          border: `3px solid ${engineerBorder}`,
          borderRadius: components.diagram.nodeBorderRadius,
          opacity: engineerOpacity,
          transform: `scale(${engineerScale})`,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          boxShadow: isOverloaded ? `0 0 30px rgba(245, 158, 11, 0.4)` : "none",
        }}
      >
        <div
          style={{
            fontFamily: typography.titleFont,
            fontSize: 32,
            fontWeight: 700,
            color: engineerTextColor,
            marginBottom: 12,
          }}
        >
          少数质量工程师
        </div>
        <div
          style={{
            fontFamily: typography.bodyFont,
            fontSize: 22,
            color: isOverloaded ? colors.warning : colors.textSecondary,
            backgroundColor: isOverloaded ? "rgba(245, 158, 11, 0.2)" : "transparent",
            padding: "4px 16px",
            borderRadius: 12,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {isOverloaded && (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          人工巡检过载
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