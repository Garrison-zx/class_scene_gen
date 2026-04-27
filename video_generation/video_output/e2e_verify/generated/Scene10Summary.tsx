import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
} from "remotion";

export const Scene10Summary: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // 全局淡出动画（最后 2 秒 = 60 帧）
  const fadeOutStart = durationInFrames - 60;
  const globalOpacity = interpolate(
    frame,
    [fadeOutStart, durationInFrames],
    [1, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  // 标题入场动画
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 20], [-30, 0], {
    extrapolateRight: "clamp",
  });

  const summaryItems = [
    "1. 装饰器本质：高阶函数",
    "2. @语法糖与 wrapper 模式",
    "3. 带参数装饰器：三层嵌套",
    "4. 最佳实践：使用 functools.wraps",
  ];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0F1729",
        opacity: globalOpacity,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 100,
          bottom: 100,
          left: 120,
          right: 120,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* 标题 */}
        <h1
          style={{
            fontFamily: "Inter",
            fontSize: 64,
            fontWeight: 700,
            color: "#FFFFFF",
            margin: 0,
            opacity: titleOpacity,
            transform: `translateY(${titleY}px)`,
          }}
        >
          课程总结
        </h1>

        {/* 总结列表容器，垂直居中以平衡画面 */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            paddingLeft: 36, // components.bullet.indent
            gap: 48,
          }}
        >
          {summaryItems.map((item, index) => {
            // 逐条出现间隔：6帧 (animations.stagger)
            const delay = 20 + index * 6;
            
            // 透明度淡入
            const itemOpacity = interpolate(
              frame,
              [delay, delay + 20],
              [0, 1],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }
            );

            // 清脆的弹性滑入动画
            const slideProgress = spring({
              frame: frame - delay,
              fps,
              config: {
                damping: 12,
                stiffness: 150,
              },
            });
            const itemY = interpolate(slideProgress, [0, 1], [60, 0]);

            return (
              <div
                key={index}
                style={{
                  display: "flex",
                  alignItems: "center",
                  opacity: itemOpacity,
                  transform: `translateY(${itemY}px)`,
                }}
              >
                {/* 列表图标 (Chevron) */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginRight: 16, // components.bullet.spacing
                  }}
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#3B82F6"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>

                {/* 列表文本 */}
                <span
                  style={{
                    fontFamily: "Inter",
                    fontSize: 28,
                    fontWeight: 400,
                    color: "#E2E8F0",
                    lineHeight: 1.5,
                  }}
                >
                  {item}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};