import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from "remotion";

export const Scene05Content: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 严格遵循 Tech Dark 风格配置
  const colors = {
    background: "#0F1729",
    primary: "#FFFFFF",
    text: "#E2E8F0",
    textSecondary: "#94A3B8",
    error: "#EF4444",
    accent: "#3B82F6"
  };

  const typography = {
    titleFont: "Inter",
    titleSize: 64,
    titleWeight: 700,
    bodyFont: "Inter",
    bodySize: 28,
    bodyWeight: 400,
    lineHeight: 1.5
  };

  const layout = {
    paddingTop: 100,
    paddingBottom: 100,
    paddingLeft: 120,
    paddingRight: 120,
  };

  const animations = {
    enterDuration: 20,
    staggerFrames: 90 // 根据提示“每条间隔 3 秒”，30fps * 3s = 90帧
  };

  // 标题入场动画
  const titleOpacity = interpolate(frame, [0, animations.enterDuration], [0, 1], { extrapolateRight: "clamp" });
  const titleY = interpolate(frame, [0, animations.enterDuration], [-30, 0], { extrapolateRight: "clamp" });

  // 进度条动画
  const progressWidth = interpolate(frame, [0, durationInFrames], [0, 1920], { extrapolateRight: "clamp" });

  const bullets = [
    { main: "1. 覆盖不足", sub: "(人手有限)" },
    { main: "2. 反应滞后", sub: "(频次有限)" },
    { main: "3. 经验依赖", sub: "(新人培养慢)" }
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: colors.background }}>
      {/* 安全区域内容 */}
      <div style={{
        position: "absolute",
        top: layout.paddingTop,
        left: layout.paddingLeft,
        right: layout.paddingRight,
        bottom: layout.paddingBottom,
        display: "flex",
        flexDirection: "column"
      }}>
        
        {/* 标题 */}
        <div style={{
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          fontFamily: typography.titleFont,
          fontSize: typography.titleSize,
          fontWeight: typography.titleWeight,
          color: colors.primary,
          lineHeight: typography.lineHeight,
          marginBottom: 80
        }}>
          人工巡检的三大痛点
        </div>

        {/* 要点列表 */}
        <div style={{ 
          display: "flex", 
          flexDirection: "column", 
          gap: 64, 
          marginLeft: 36 // components.bullet.indent
        }}>
          {bullets.map((bullet, index) => {
            // 延迟计算：标题动画后开始，每条间隔 90 帧
            const delay = animations.enterDuration + 10 + index * animations.staggerFrames;
            
            const itemOpacity = interpolate(frame, [delay, delay + animations.enterDuration], [0, 1], { 
              extrapolateLeft: "clamp", 
              extrapolateRight: "clamp" 
            });
            const itemX = interpolate(frame, [delay, delay + animations.enterDuration], [-60, 0], { 
              extrapolateLeft: "clamp", 
              extrapolateRight: "clamp" 
            });

            return (
              <div key={index} style={{
                display: "flex",
                alignItems: "center",
                opacity: itemOpacity,
                transform: `translateX(${itemX}px)`,
                gap: 24
              }}>
                {/* 红色警示图标 */}
                <div style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  width: 48,
                  height: 48,
                  backgroundColor: "rgba(239, 68, 68, 0.1)",
                  borderRadius: 12
                }}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={colors.error} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                </div>

                {/* 文字内容 */}
                <div style={{ 
                  display: "flex", 
                  alignItems: "baseline", 
                  gap: 16 // components.bullet.spacing
                }}>
                  <span style={{
                    fontFamily: typography.bodyFont,
                    fontSize: typography.bodySize + 8, // 略微放大主标题以增强视觉层级
                    fontWeight: 700,
                    color: colors.text,
                    lineHeight: typography.lineHeight
                  }}>
                    {bullet.main}
                  </span>
                  <span style={{
                    fontFamily: typography.bodyFont,
                    fontSize: typography.bodySize,
                    fontWeight: typography.bodyWeight,
                    color: colors.textSecondary,
                    lineHeight: typography.lineHeight
                  }}>
                    {bullet.sub}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 底部进度条 (components.progressBar) */}
      <div style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        width: "100%",
        height: 3,
        backgroundColor: "rgba(255,255,255,0.1)"
      }}>
        <div style={{
          width: progressWidth,
          height: "100%",
          backgroundColor: colors.accent
        }} />
      </div>
    </AbsoluteFill>
  );
};