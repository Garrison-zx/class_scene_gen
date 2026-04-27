import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
  Easing,
} from "remotion";

export const Scene01Title: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 动画时长配置
  const enterDuration = 20;
  const subtitleDelay = 15; // 0.5秒 @ 30fps

  // 大标题动画：从中央放大淡入
  const titleOpacity = interpolate(frame, [0, enterDuration], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const titleScale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });

  // 副标题动画：延迟0.5秒从下方滑入
  const subtitleOpacity = interpolate(
    frame,
    [subtitleDelay, subtitleDelay + enterDuration],
    [0, 1],
    {
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    }
  );
  const subtitleY = interpolate(
    frame,
    [subtitleDelay, subtitleDelay + enterDuration],
    [40, 0],
    {
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );

  // 背景呼吸渐变动画
  const breath = (Math.sin(frame / 45) + 1) / 2;
  const gradientScale = interpolate(breath, [0, 1], [1, 1.2]);
  const gradientOpacity = interpolate(breath, [0, 1], [0.15, 0.25]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0F1729", // colors.background
        overflow: "hidden",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* 呼吸渐变背景 */}
      <div
        style={{
          position: "absolute",
          width: "150%",
          height: "150%",
          background: "radial-gradient(circle, #3B82F6 0%, transparent 60%)", // colors.accent
          opacity: gradientOpacity,
          transform: `scale(${gradientScale})`,
          top: "-25%",
          left: "-25%",
        }}
      />

      {/* Python 官方 Logo 水印 (纯SVG绘制) */}
      <svg
        viewBox="0 0 110 110"
        style={{
          width: 800,
          height: 800,
          opacity: 0.03,
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
        }}
      >
        <path
          d="M 55 5 C 25 5 25 25 25 25 L 25 35 L 55 35 L 55 40 L 15 40 C 5 40 5 65 5 65 C 5 85 20 85 20 85 L 30 85 L 30 75 C 30 60 40 50 55 50 L 75 50 C 85 50 85 35 85 35 C 85 15 65 5 55 5 Z"
          fill="#FFFFFF"
        />
        <path
          d="M 55 105 C 85 105 85 85 85 85 L 85 75 L 55 75 L 55 70 L 95 70 C 105 70 105 45 105 45 C 105 25 90 25 90 25 L 80 25 L 80 35 C 80 50 70 60 55 60 L 35 60 C 25 60 25 75 25 75 C 25 95 45 105 55 105 Z"
          fill="#FFFFFF"
        />
        <circle cx="40" cy="20" r="4" fill="#0F1729" />
        <circle cx="70" cy="90" r="4" fill="#0F1729" />
      </svg>

      {/* 内容安全区域 */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 10,
          paddingTop: 100,
          paddingBottom: 100,
          paddingLeft: 120,
          paddingRight: 120,
          width: "100%",
          maxWidth: 1400,
        }}
      >
        {/* 大标题 */}
        <h1
          style={{
            fontFamily: "Inter",
            fontSize: 64,
            fontWeight: 700,
            color: "#FFFFFF", // colors.primary
            margin: 0,
            opacity: titleOpacity,
            transform: `scale(${titleScale})`,
            textAlign: "center",
            lineHeight: 1.5,
            letterSpacing: "0.05em",
          }}
        >
          Python 装饰器核心解析
        </h1>

        {/* 副标题 */}
        <h2
          style={{
            fontFamily: "Inter",
            fontSize: 28,
            fontWeight: 400,
            color: "#94A3B8", // colors.textSecondary
            marginTop: 24,
            opacity: subtitleOpacity,
            transform: `translateY(${subtitleY}px)`,
            textAlign: "center",
            lineHeight: 1.5,
            letterSpacing: "0.02em",
          }}
        >
          从本质到高阶用法
        </h2>
      </div>
    </AbsoluteFill>
  );
};