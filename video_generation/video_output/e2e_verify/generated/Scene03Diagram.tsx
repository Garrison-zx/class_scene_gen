import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
  Easing,
} from "remotion";

export const Scene03Diagram: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 风格配置
  const colors = {
    background: "#0F1729",
    primary: "#FFFFFF",
    secondary: "#94A3B8",
    accent: "#3B82F6",
    text: "#E2E8F0",
    textSecondary: "#94A3B8",
    nodeBackground: "#1E293B",
    nodeBorder: "#334155",
    arrowColor: "#94A3B8",
  };

  const typography = {
    titleFont: "Inter",
    titleSize: 64,
    titleWeight: 700,
    bodyFont: "Inter",
    bodySize: 28,
    codeFont: "JetBrains Mono",
    codeSize: 22,
  };

  // 动画计算
  // 1. 标题淡入 (0-20帧)
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 2. 节点1 (原函数) 出现 (20-40帧)
  const node1Opacity = interpolate(frame, [20, 40], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  
  // 节点1 移动到节点2内部 (100-130帧)
  const node1X = interpolate(frame, [100, 130], [400, 960], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // 3. 箭头1 伸展 (50-70帧)
  const arrow1Progress = interpolate(frame, [50, 70], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // 节点1移动时，箭头1淡出
  const arrow1Opacity = interpolate(frame, [100, 115], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // 4. 节点2 (装饰器) 出现 (70-90帧)
  const node2Opacity = interpolate(frame, [70, 90], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const node2Scale = spring({
    frame: frame - 70,
    fps,
    config: { damping: 12, stiffness: 100 },
  });
  
  // 节点2 处理动画 (130-160帧)
  const node2ProcessPulse = interpolate(frame, [130, 145, 160], [1, 1.05, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const node2Glow = interpolate(frame, [130, 145, 160], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // 5. 箭头2 伸展 (160-180帧)
  const arrow2Progress = interpolate(frame, [160, 180], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // 6. 节点3 (增强函数) 出现 (180-200帧)
  const node3Opacity = interpolate(frame, [180, 200], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const node3Scale = spring({
    frame: frame - 180,
    fps,
    config: { damping: 12, stiffness: 100 },
  });
  
  // 节点3 持续闪烁发光 (200帧以后)
  const node3Glow = frame > 200 ? Math.sin((frame - 200) * 0.15) * 0.5 + 0.5 : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.background }}>
      {/* 标题区域 */}
      <div
        style={{
          position: "absolute",
          top: 100,
          left: 120,
          opacity: titleOpacity,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <h1
          style={{
            margin: 0,
            fontFamily: typography.titleFont,
            fontSize: typography.titleSize,
            fontWeight: typography.titleWeight,
            color: colors.primary,
          }}
        >
          装饰器工作原理
        </h1>
        <h2
          style={{
            margin: 0,
            fontFamily: typography.bodyFont,
            fontSize: typography.bodySize,
            color: colors.textSecondary,
            fontWeight: 400,
          }}
        >
          工作流程图
        </h2>
      </div>

      {/* 流程图区域 */}
      <div style={{ position: "absolute", top: 0, left: 0, width: 1920, height: 1080 }}>
        
        {/* 箭头 1 (原函数 -> 装饰器) */}
        <svg
          style={{
            position: "absolute",
            left: 520,
            top: 530,
            width: 260,
            height: 20,
            opacity: arrow1Opacity,
            zIndex: 1,
          }}
        >
          <line
            x1={0}
            y1={10}
            x2={260 * arrow1Progress}
            y2={10}
            stroke={colors.arrowColor}
            strokeWidth={4}
          />
          {arrow1Progress > 0.05 && (
            <polygon
              points={`${260 * arrow1Progress},10 ${260 * arrow1Progress - 12},4 ${
                260 * arrow1Progress - 12
              },16`}
              fill={colors.arrowColor}
            />
          )}
        </svg>

        {/* 箭头 2 (装饰器 -> 增强函数) */}
        <svg
          style={{
            position: "absolute",
            left: 1140,
            top: 530,
            width: 260,
            height: 20,
            zIndex: 1,
          }}
        >
          <line
            x1={0}
            y1={10}
            x2={260 * arrow2Progress}
            y2={10}
            stroke={colors.arrowColor}
            strokeWidth={4}
          />
          {arrow2Progress > 0.05 && (
            <polygon
              points={`${260 * arrow2Progress},10 ${260 * arrow2Progress - 12},4 ${
                260 * arrow2Progress - 12
              },16`}
              fill={colors.arrowColor}
            />
          )}
        </svg>

        {/* 节点 2: 装饰器 (大方框) */}
        <div
          style={{
            position: "absolute",
            left: 960 - 160,
            top: 540 - 120,
            width: 320,
            height: 240,
            opacity: node2Opacity,
            transform: `scale(${Math.max(0, node2Scale * node2ProcessPulse)})`,
            backgroundColor: "rgba(30, 41, 59, 0.4)",
            border: `3px dashed ${colors.accent}`,
            borderRadius: 16,
            zIndex: 5,
            boxShadow: `0 0 ${40 * node2Glow}px rgba(59, 130, 246, ${node2Glow * 0.6})`,
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "center",
            paddingTop: 20,
            boxSizing: "border-box",
          }}
        >
          <span
            style={{
              color: colors.accent,
              fontFamily: typography.codeFont,
              fontSize: typography.codeSize,
              fontWeight: 600,
            }}
          >
            @decorator
          </span>
        </div>

        {/* 节点 1: 原函数 */}
        <div
          style={{
            position: "absolute",
            left: node1X - 100,
            top: 540 - 60,
            width: 200,
            height: 120,
            opacity: node1Opacity,
            backgroundColor: colors.nodeBackground,
            border: `2px solid ${colors.nodeBorder}`,
            borderRadius: 12,
            zIndex: 10,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
          }}
        >
          <span
            style={{
              color: colors.text,
              fontFamily: typography.bodyFont,
              fontSize: 24,
              fontWeight: 600,
            }}
          >
            原函数
          </span>
          <span
            style={{
              color: colors.accent,
              fontFamily: typography.codeFont,
              fontSize: 20,
              marginTop: 8,
            }}
          >
            func()
          </span>
        </div>

        {/* 节点 3: 增强函数 */}
        <div
          style={{
            position: "absolute",
            left: 1520 - 100,
            top: 540 - 60,
            width: 200,
            height: 120,
            opacity: node3Opacity,
            transform: `scale(${Math.max(0, node3Scale)})`,
            backgroundColor: colors.nodeBackground,
            border: `2px solid ${colors.accent}`,
            borderRadius: 12,
            zIndex: 10,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: `0 0 ${20 + 30 * node3Glow}px rgba(59, 130, 246, ${
              0.4 + 0.6 * node3Glow
            })`,
          }}
        >
          <span
            style={{
              color: colors.text,
              fontFamily: typography.bodyFont,
              fontSize: 24,
              fontWeight: 600,
            }}
          >
            增强函数
          </span>
          <span
            style={{
              color: colors.accent,
              fontFamily: typography.codeFont,
              fontSize: 20,
              marginTop: 8,
            }}
          >
            wrapper()
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};