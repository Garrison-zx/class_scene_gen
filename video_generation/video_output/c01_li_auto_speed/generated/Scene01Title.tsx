import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
} from "remotion";

export const Scene01Title: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 风格配置数据
  const colors = {
    background: "#0F1729",
    primary: "#FFFFFF",
    accent: "#3B82F6",
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
    padding: "100px 120px",
  };

  const animations = {
    enterDuration: 20,
  };

  // 动画计算：大标题从中央放大淡入
  const titleOpacity = interpolate(
    frame,
    [0, animations.enterDuration],
    [0, 1],
    { extrapolateRight: "clamp" }
  );

  const titleSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120 },
  });
  
  const titleScale = interpolate(titleSpring, [0, 1], [0.8, 1]);

  // 动画计算：副标题延迟 0.5 秒 (15帧) 从下方滑入
  const subtitleDelay = 15;
  const subtitleOpacity = interpolate(
    frame,
    [subtitleDelay, subtitleDelay + animations.enterDuration],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  
  const subtitleY = interpolate(
    frame,
    [subtitleDelay, subtitleDelay + animations.enterDuration],
    [40, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        // 深蓝色科技感渐变背景，使用 background 和 accent 颜色
        background: `radial-gradient(circle at center, rgba(59, 130, 246, 0.15) 0%, ${colors.background} 70%)`,
        backgroundColor: colors.background,
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        padding: layout.padding,
      }}
    >
      {/* 大标题 */}
      <div
        style={{
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
          fontFamily: typography.titleFont,
          fontSize: `${typography.titleSize}px`,
          fontWeight: typography.titleWeight,
          color: colors.primary,
          textAlign: "center",
          marginBottom: "32px",
          lineHeight: 1.2,
          letterSpacing: "0.02em",
        }}
      >
        制造业AI转型的真正挑战
      </div>

      {/* 副标题 */}
      <div
        style={{
          opacity: subtitleOpacity,
          transform: `translateY(${subtitleY}px)`,
          fontFamily: typography.bodyFont,
          fontSize: `${typography.bodySize}px`,
          fontWeight: typography.bodyWeight,
          color: colors.textSecondary,
          textAlign: "center",
          // 蓝色光晕效果
          textShadow: `0 0 15px rgba(59, 130, 246, 0.8), 0 0 30px rgba(59, 130, 246, 0.4)`,
          letterSpacing: "0.05em",
        }}
      >
        突破“专家瓶颈”与生产力天花板
      </div>
    </AbsoluteFill>
  );
};