import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  AbsoluteFill,
  Easing,
} from "remotion";

export const Scene03Transition: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  // 风格配置提取
  const colors = {
    background: "#0F1729",
    primary: "#FFFFFF",
    accent: "#3B82F6",
    secondary: "#94A3B8",
  };

  const typography = {
    titleFont: "Inter",
    titleSize: 64,
    titleWeight: 700,
  };

  const animations = {
    enterDuration: 20,
    exitDuration: 15,
  };

  // 动画计算
  // 1. 文字从左至右擦除出现 (clip-path inset right)
  const wipeRightInset = interpolate(
    frame,
    [0, animations.enterDuration],
    [100, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    }
  );

  // 2. 整体画面在结尾向左平移切出
  const exitStartFrame = durationInFrames - animations.exitDuration;
  const sceneTranslateX = interpolate(
    frame,
    [exitStartFrame, durationInFrames],
    [0, -width],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.background,
        transform: `translateX(${sceneTranslateX}px)`,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {/* 微弱的网格线背景 */}
      <svg
        width="100%"
        height="100%"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          opacity: 0.1,
        }}
      >
        <defs>
          <pattern
            id="transition-grid"
            width="80"
            height="80"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 80 0 L 0 0 0 80"
              fill="none"
              stroke={colors.secondary}
              strokeWidth="1"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#transition-grid)" />
      </svg>

      {/* 全屏过渡文字 */}
      <div
        style={{
          fontFamily: typography.titleFont,
          fontSize: `${typography.titleSize}px`,
          fontWeight: typography.titleWeight,
          color: colors.primary,
          clipPath: `inset(0 ${wipeRightInset}% 0 0)`,
          whiteSpace: "nowrap",
          zIndex: 1,
          // 稍微发光增加科技感
          textShadow: `0 0 20px rgba(255, 255, 255, 0.1)`,
        }}
      >
        <span style={{ color: colors.accent }}>2020年</span> 理想汽车的质量管理困境
      </div>
    </AbsoluteFill>
  );
};