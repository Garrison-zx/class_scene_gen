import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  AbsoluteFill,
} from "remotion";

export const Scene05Code: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 动画时长配置
  const enterDuration = 20;
  const exitDuration = 15;
  const stagger = 6;

  // 场景淡入淡出
  const enterOpacity = interpolate(frame, [0, enterDuration], [0, 1], {
    extrapolateRight: "clamp",
  });
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - exitDuration, durationInFrames],
    [1, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );
  const sceneOpacity = Math.min(enterOpacity, exitOpacity);

  // 进度条
  const progressWidth = interpolate(frame, [0, durationInFrames], [0, 1920], {
    extrapolateRight: "clamp",
  });

  // 包装器高亮 (Lines 1-5) 帧区间: 150 - 280
  const wrapperHighlightOpacity = interpolate(
    frame,
    [150, 160, 270, 280],
    [0, 1, 1, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  // 装饰器语法闪烁高亮 (Line 8) 帧区间: 300起
  const decoratorBlinkOpacity = interpolate(
    frame,
    [300, 305, 310, 315, 320, 325, 330],
    [0, 1, 0, 1, 0, 1, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  // 代码行数据与语法高亮渲染
  const codeLines = [
    {
      content: (
        <>
          <span style={{ color: "#3B82F6" }}>def</span>{" "}
          <span style={{ color: "#F59E0B" }}>my_decorator</span>(func):
        </>
      ),
    },
    {
      content: (
        <>
          {"    "}
          <span style={{ color: "#3B82F6" }}>def</span>{" "}
          <span style={{ color: "#F59E0B" }}>wrapper</span>(*args, **kwargs):
        </>
      ),
    },
    {
      content: (
        <>
          {"        "}
          <span style={{ color: "#F59E0B" }}>print</span>(
          <span style={{ color: "#22C55E" }}>&quot;调用前&quot;</span>)
        </>
      ),
    },
    {
      content: (
        <>
          {"        "}result = func(*args, **kwargs)
        </>
      ),
    },
    {
      content: (
        <>
          {"        "}
          <span style={{ color: "#F59E0B" }}>print</span>(
          <span style={{ color: "#22C55E" }}>&quot;调用后&quot;</span>)
        </>
      ),
    },
    {
      content: (
        <>
          {"        "}
          <span style={{ color: "#3B82F6" }}>return</span> result
        </>
      ),
    },
    {
      content: (
        <>
          {"    "}
          <span style={{ color: "#3B82F6" }}>return</span> wrapper
        </>
      ),
    },
    {
      content: <></>,
    },
    {
      content: (
        <>
          <span style={{ color: "#3B82F6" }}>@my_decorator</span>
        </>
      ),
    },
    {
      content: (
        <>
          <span style={{ color: "#3B82F6" }}>def</span>{" "}
          <span style={{ color: "#F59E0B" }}>say_hello</span>(name):
        </>
      ),
    },
    {
      content: (
        <>
          {"    "}
          <span style={{ color: "#F59E0B" }}>print</span>(
          <span style={{ color: "#22C55E" }}>f&quot;Hello, {"{name}"}!&quot;</span>)
        </>
      ),
    },
  ];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0F1729",
        opacity: sceneOpacity,
        fontFamily: "Inter, sans-serif",
      }}
    >
      {/* 标题 */}
      <div
        style={{
          position: "absolute",
          top: 100,
          left: 120,
          fontSize: 64,
          fontWeight: 700,
          color: "#FFFFFF",
          transform: `translateY(${interpolate(
            frame,
            [0, enterDuration],
            [-20, 0],
            { extrapolateRight: "clamp" }
          )}px)`,
        }}
      >
        基本语法
      </div>

      {/* 代码块容器 */}
      <div
        style={{
          position: "absolute",
          top: 220,
          left: 120,
          width: 1400,
          backgroundColor: "#1E293B",
          borderRadius: 12,
          padding: "32px 0",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
        }}
      >
        {codeLines.map((line, index) => {
          // 逐行出现动画
          const delay = enterDuration + index * stagger;
          const lineOpacity = interpolate(
            frame,
            [delay, delay + 15],
            [0, 1],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }
          );
          const lineTranslateX = interpolate(
            frame,
            [delay, delay + 15],
            [-20, 0],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }
          );

          // 计算当前行的高亮背景
          let bgOpacity = 0;
          if (index >= 1 && index <= 5) {
            bgOpacity = wrapperHighlightOpacity;
          } else if (index === 8) {
            bgOpacity = decoratorBlinkOpacity;
          }

          return (
            <div
              key={index}
              style={{
                display: "flex",
                opacity: lineOpacity,
                transform: `translateX(${lineTranslateX}px)`,
                backgroundColor: `rgba(59, 130, 246, ${bgOpacity * 0.15})`,
                padding: "4px 32px",
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: 22,
                lineHeight: 1.5,
                color: "#E2E8F0",
                whiteSpace: "pre",
                transition: "background-color 0.1s ease",
              }}
            >
              <div
                style={{
                  width: 40,
                  textAlign: "right",
                  marginRight: 24,
                  color: "#475569",
                  userSelect: "none",
                }}
              >
                {index + 1}
              </div>
              <div>{line.content}</div>
            </div>
          );
        })}
      </div>

      {/* 底部进度条 */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: 1920,
          height: 3,
          backgroundColor: "rgba(255,255,255,0.1)",
        }}
      >
        <div
          style={{
            height: "100%",
            width: progressWidth,
            backgroundColor: "#3B82F6",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};