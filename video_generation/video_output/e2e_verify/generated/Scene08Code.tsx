import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill, Easing } from "remotion";

export const Scene08Code: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, durationInFrames } = useVideoConfig();

  const easeInOutCubic = Easing.inOut(Easing.cubic);

  // 标题入场动画
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], { 
    extrapolateRight: "clamp",
    easing: easeInOutCubic
  });
  const titleY = interpolate(frame, [0, 20], [20, 0], { 
    extrapolateRight: "clamp",
    easing: easeInOutCubic
  });

  // 代码块容器入场动画
  const codeBlockOpacity = interpolate(frame, [10, 30], [0, 1], { 
    extrapolateRight: "clamp",
    easing: easeInOutCubic
  });
  const codeBlockY = interpolate(frame, [10, 30], [20, 0], { 
    extrapolateRight: "clamp",
    easing: easeInOutCubic
  });

  // 代码行数据，按层级分组以实现逐层出现的动画
  const codeLines = [
    { num: 1, group: 0, content: <><span style={{color: '#3B82F6'}}>def</span> <span style={{color: '#F59E0B'}}>repeat</span>(n):</> },
    { num: 2, group: 1, content: <>{"    "}<span style={{color: '#3B82F6'}}>def</span> <span style={{color: '#F59E0B'}}>decorator</span>(func):</> },
    { num: 3, group: 2, content: <>{"        "}<span style={{color: '#3B82F6'}}>def</span> <span style={{color: '#F59E0B'}}>wrapper</span>(*args, **kwargs):</> },
    { num: 4, group: 2, content: <>{"            "}<span style={{color: '#3B82F6'}}>for</span> _ <span style={{color: '#3B82F6'}}>in</span> <span style={{color: '#F59E0B'}}>range</span>(n):</> },
    { num: 5, group: 2, content: <>{"                "}result = func(*args, **kwargs)</> },
    { num: 6, group: 2, content: <>{"            "}<span style={{color: '#3B82F6'}}>return</span> result</> },
    { num: 7, group: 1, content: <>{"        "}<span style={{color: '#3B82F6'}}>return</span> wrapper</> },
    { num: 8, group: 0, content: <>{"    "}<span style={{color: '#3B82F6'}}>return</span> decorator</> },
    { num: 9, group: 3, content: <></> },
    { num: 10, group: 3, content: <><span style={{color: '#3B82F6'}}>@repeat</span>(3)</> },
    { num: 11, group: 3, content: <><span style={{color: '#3B82F6'}}>def</span> <span style={{color: '#F59E0B'}}>greet</span>():</> },
    { num: 12, group: 3, content: <>{"    "}<span style={{color: '#F59E0B'}}>print</span>(<span style={{color: '#22C55E'}}>"Hello!"</span>)</> },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: "#0F1729" }}>
      {/* 标题 */}
      <div style={{
        position: "absolute",
        top: 100,
        left: 120,
        opacity: titleOpacity,
        transform: `translateY(${titleY}px)`,
        fontFamily: "Inter",
        fontSize: 64,
        fontWeight: 700,
        color: "#FFFFFF"
      }}>
        带参数的装饰器
      </div>

      {/* 代码块 */}
      <div style={{
        position: "absolute",
        top: 220,
        left: 120,
        width: 1680,
        backgroundColor: "#1E293B",
        borderRadius: 12,
        padding: 32,
        opacity: codeBlockOpacity,
        transform: `translateY(${codeBlockY}px)`,
        fontFamily: "JetBrains Mono",
        fontSize: 22,
        lineHeight: 1.5,
        color: "#E2E8F0"
      }}>
        {codeLines.map((line, i) => {
          // 逐层出现的延迟计算 (stagger: 6 frames per layer, base delay: 30)
          const delay = 30 + line.group * 15;
          const lineOpacity = interpolate(frame, [delay, delay + 15], [0, 1], { 
            extrapolateLeft: "clamp", 
            extrapolateRight: "clamp",
            easing: easeInOutCubic
          });
          const lineX = interpolate(frame, [delay, delay + 15], [-20, 0], { 
            extrapolateLeft: "clamp", 
            extrapolateRight: "clamp",
            easing: easeInOutCubic
          });

          // 行高亮逻辑
          let highlightOpacity = 0;
          if (line.num === 1) {
            // 高亮 def repeat(n):
            const fadeIn = interpolate(frame, [120, 135], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeInOutCubic });
            const fadeOut = interpolate(frame, [265, 280], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeInOutCubic });
            highlightOpacity = Math.min(fadeIn, fadeOut);
          } else if (line.num === 10) {
            // 高亮 @repeat(3)
            const fadeIn = interpolate(frame, [300, 315], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeInOutCubic });
            const fadeOut = interpolate(frame, [445, 460], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeInOutCubic });
            highlightOpacity = Math.min(fadeIn, fadeOut);
          }

          return (
            <div key={i} style={{
              display: "flex",
              opacity: lineOpacity,
              transform: `translateX(${lineX}px)`,
              backgroundColor: `rgba(59, 130, 246, ${highlightOpacity * 0.15})`,
              borderRadius: 4,
              padding: "2px 8px",
              marginLeft: "-8px",
              marginRight: "-8px"
            }}>
              <div style={{
                width: 40,
                textAlign: "right",
                marginRight: 24,
                color: "#475569",
                userSelect: "none"
              }}>
                {line.num}
              </div>
              <div style={{ whiteSpace: "pre" }}>
                {line.content}
              </div>
            </div>
          );
        })}
      </div>

      {/* 底部进度条 */}
      <div style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        width: width,
        height: 3,
        backgroundColor: "rgba(255,255,255,0.1)"
      }}>
        <div style={{
          height: "100%",
          backgroundColor: "#3B82F6",
          width: interpolate(frame, [0, durationInFrames], [0, width], { extrapolateRight: "clamp" })
        }} />
      </div>
    </AbsoluteFill>
  );
};