import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  AbsoluteFill,
  Easing,
} from "remotion";

export const Scene06Transition: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 动画配置参数
  const enterDuration = 20;
  const exitDuration = 15;
  const exitStart = durationInFrames - exitDuration;

  // 透明度：淡入 + 淡出
  const opacityIn = interpolate(frame, [0, enterDuration], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const opacityOut = interpolate(
    frame,
    [exitStart, durationInFrames],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    }
  );
  const opacity = opacityIn - opacityOut;

  // 文字轻微放大效果 (0.95 -> 1.05)
  const textScale = interpolate(frame, [0, durationInFrames], [0.95, 1.05], {
    extrapolateRight: "clamp",
  });

  // 背景暗纹缓慢旋转效果
  const bgRotation = interpolate(frame, [0, durationInFrames], [0, 10], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0F1729", overflow: "hidden" }}>
      {/* 背景暗纹：网络连接/齿轮抽象图案 */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: 1200,
          height: 1200,
          marginLeft: -600,
          marginTop: -600,
          opacity: 0.08,
          transform: `rotate(${bgRotation}deg)`,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 800 800"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            cx="400"
            cy="400"
            r="350"
            stroke="#94A3B8"
            strokeWidth="2"
            strokeDasharray="15 15"
          />
          <circle cx="400" cy="400" r="250" stroke="#94A3B8" strokeWidth="1" />
          <circle
            cx="400"
            cy="400"
            r="150"
            stroke="#94A3B8"
            strokeWidth="2"
            strokeDasharray="5 10"
          />
          <path
            d="M400 50 L400 750 M50 400 L750 400 M152 152 L648 648 M152 648 L648 152"
            stroke="#94A3B8"
            strokeWidth="1"
          />
          {/* 节点 */}
          <circle cx="400" cy="50" r="8" fill="#3B82F6" />
          <circle cx="400" cy="750" r="8" fill="#3B82F6" />
          <circle cx="50" cy="400" r="8" fill="#3B82F6" />
          <circle cx="750" cy="400" r="8" fill="#3B82F6" />
          <circle cx="152" cy="152" r="8" fill="#3B82F6" />
          <circle cx="648" cy="648" r="8" fill="#3B82F6" />
          <circle cx="152" cy="648" r="8" fill="#3B82F6" />
          <circle cx="648" cy="152" r="8" fill="#3B82F6" />
          <circle cx="400" cy="400" r="12" fill="#3B82F6" />
        </svg>
      </div>

      {/* 中心文字内容 */}
      <div
        style={{
          position: "absolute",
          top: 100,
          bottom: 100,
          left: 120,
          right: 120,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <h1
          style={{
            fontFamily: "Inter",
            fontSize: 64,
            fontWeight: 700,
            color: "#FFFFFF",
            margin: 0,
            opacity: opacity,
            transform: `scale(${textScale})`,
            textAlign: "center",
            letterSpacing: "0.05em",
            textShadow: "0 4px 24px rgba(0, 0, 0, 0.5)",
          }}
        >
          危机蔓延：售后与供应链
        </h1>
      </div>
    </AbsoluteFill>
  );
};