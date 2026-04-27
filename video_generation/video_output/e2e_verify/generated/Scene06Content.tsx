import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
} from "remotion";

export const Scene06Content: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 标题入场动画
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 20], [-20, 0], {
    extrapolateRight: "clamp",
  });

  // 卡片数据与时间轴配置
  const cards = [
    {
      id: "timer",
      title: "计时器",
      subtitle: "Timer",
      highlightStart: 90,
      highlightEnd: 180,
      icon: (color: string) => (
        <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="14" r="8"></circle>
          <polyline points="12 10 12 14 14 16"></polyline>
          <line x1="12" y1="2" x2="12" y2="4"></line>
          <line x1="10" y1="2" x2="14" y2="2"></line>
        </svg>
      ),
    },
    {
      id: "logger",
      title: "日志",
      subtitle: "Logger",
      highlightStart: 180,
      highlightEnd: 270,
      icon: (color: string) => (
        <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
      ),
    },
    {
      id: "cache",
      title: "缓存",
      subtitle: "Cache",
      highlightStart: 270,
      highlightEnd: 435, // 延长结束时间使其保持高亮直到场景结束
      icon: (color: string) => (
        <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
        </svg>
      ),
    },
  ];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0F1729",
        paddingTop: "100px",
        paddingBottom: "100px",
        paddingLeft: "120px",
        paddingRight: "120px",
      }}
    >
      {/* 标题 */}
      <div
        style={{
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          fontFamily: "Inter",
          fontSize: "64px",
          fontWeight: 700,
          color: "#FFFFFF",
          marginBottom: "120px",
        }}
      >
        典型应用场景
      </div>

      {/* 卡片容器 */}
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "space-between",
          gap: "60px",
          width: "100%",
          height: "560px",
        }}
      >
        {cards.map((card, index) => {
          // 入场动画 (Staggered)
          const entryDelay = 20 + index * 6;
          const entryProgress = spring({
            frame: Math.max(0, frame - entryDelay),
            fps,
            config: { damping: 14, stiffness: 120 },
          });
          const translateY = interpolate(entryProgress, [0, 1], [150, 0]);
          const opacity = entryProgress;

          // 高亮状态插值
          const highlightProgress = interpolate(
            frame,
            [
              card.highlightStart,
              card.highlightStart + 15,
              card.highlightEnd - 15,
              card.highlightEnd,
            ],
            [0, 1, 1, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );

          // 缩放效果
          const scale = 1 + highlightProgress * 0.05;

          return (
            <div
              key={card.id}
              style={{
                flex: 1,
                backgroundColor: "#1E293B",
                borderRadius: "12px",
                border: "2px solid #334155",
                opacity,
                transform: `translateY(${translateY}px) scale(${scale})`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                position: "relative",
              }}
            >
              {/* 高亮边框与发光效果 */}
              <div
                style={{
                  position: "absolute",
                  inset: -2,
                  borderRadius: "12px",
                  border: "2px solid #3B82F6",
                  opacity: highlightProgress,
                  boxShadow: "0 0 40px rgba(59, 130, 246, 0.2)",
                  pointerEvents: "none",
                }}
              />

              {/* 图标 (通过透明度实现颜色渐变) */}
              <div
                style={{
                  position: "relative",
                  width: "100px",
                  height: "100px",
                  marginBottom: "40px",
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    opacity: 1 - highlightProgress,
                  }}
                >
                  {card.icon("#94A3B8")}
                </div>
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    opacity: highlightProgress,
                  }}
                >
                  {card.icon("#3B82F6")}
                </div>
              </div>

              {/* 卡片标题 */}
              <div
                style={{
                  fontFamily: "Inter",
                  fontSize: "40px",
                  fontWeight: 700,
                  color: "#FFFFFF",
                  marginBottom: "16px",
                }}
              >
                {card.title}
              </div>
              
              {/* 卡片副标题 */}
              <div
                style={{
                  fontFamily: "Inter",
                  fontSize: "28px",
                  fontWeight: 400,
                  color: "#94A3B8",
                }}
              >
                {card.subtitle}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};