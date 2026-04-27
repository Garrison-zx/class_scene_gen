import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
  Easing,
} from "remotion";

export const Scene07Transition: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 动画配置参数
  const enterDuration = 20;
  const stagger = 6;

  // 整体淡入与上浮动画
  const containerOpacity = interpolate(frame, [0, enterDuration], [0, 1], {
    extrapolateRight: "clamp",
  });
  const containerY = interpolate(frame, [0, enterDuration], [40, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });

  // 图标弹性缩放动画
  const iconScale = spring({
    frame: frame - stagger,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  // 文字弹性缩放动画
  const textScale = spring({
    frame: frame - stagger * 2,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  // 齿轮缓慢持续转动
  const gearRotation = interpolate(frame, [0, 240], [0, 120], {
    extrapolateRight: "clamp",
  });

  // 旋钮分段调节转动（象征参数调节）
  const knobTurn1 = interpolate(frame, [45, 75], [0, 135], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const knobTurn2 = interpolate(frame, [115, 145], [0, -60], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const knobTurn3 = interpolate(frame, [185, 215], [0, 105], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const totalKnobRotation = knobTurn1 + knobTurn2 + knobTurn3;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0F1729",
        justifyContent: "center",
        alignItems: "center",
        padding: "100px 120px",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "64px",
          opacity: containerOpacity,
          transform: `translateY(${containerY}px)`,
        }}
      >
        {/* 齿轮与旋钮图标 */}
        <div
          style={{
            width: "240px",
            height: "240px",
            transform: `scale(${iconScale})`,
            position: "relative",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          {/* 外层发光效果 */}
          <div
            style={{
              position: "absolute",
              width: "100%",
              height: "100%",
              borderRadius: "50%",
              background: "radial-gradient(circle, rgba(59,130,246,0.2) 0%, rgba(15,23,41,0) 70%)",
            }}
          />
          
          <svg width="200" height="200" viewBox="0 0 100 100" style={{ overflow: "visible" }}>
            {/* 外层齿轮 */}
            <g
              style={{
                transform: `rotate(${gearRotation}deg)`,
                transformOrigin: "50px 50px",
              }}
            >
              <circle
                cx="50"
                cy="50"
                r="42"
                stroke="#3B82F6"
                strokeWidth="12"
                strokeDasharray="14 12.3"
                fill="none"
              />
              <circle
                cx="50"
                cy="50"
                r="34"
                stroke="#1E293B"
                strokeWidth="4"
                fill="none"
              />
            </g>

            {/* 内层调节旋钮 */}
            <g
              style={{
                transform: `rotate(${totalKnobRotation}deg)`,
                transformOrigin: "50px 50px",
              }}
            >
              {/* 旋钮底座 */}
              <circle
                cx="50"
                cy="50"
                r="26"
                fill="#1E293B"
                stroke="#94A3B8"
                strokeWidth="4"
              />
              {/* 旋钮刻度线/指示器 */}
              <line
                x1="50"
                y1="50"
                x2="50"
                y2="28"
                stroke="#22C55E"
                strokeWidth="4"
                strokeLinecap="round"
              />
              {/* 旋钮中心点 */}
              <circle cx="50" cy="50" r="8" fill="#FFFFFF" />
            </g>
          </svg>
        </div>

        {/* 标题文字 */}
        <h1
          style={{
            fontFamily: "Inter",
            fontSize: "64px",
            fontWeight: 700,
            color: "#FFFFFF",
            margin: 0,
            transform: `scale(${textScale})`,
            textAlign: "center",
            letterSpacing: "2px",
            textShadow: "0 4px 24px rgba(0,0,0,0.5)",
          }}
        >
          进阶：带参数的装饰器
        </h1>
      </div>
    </AbsoluteFill>
  );
};