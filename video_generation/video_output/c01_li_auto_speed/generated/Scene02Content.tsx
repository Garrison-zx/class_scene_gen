import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
  Easing,
} from "remotion";

export const Scene02Content: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 动画参数
  const enterDuration = 20;
  const stagger = 6;
  const scaleTipFrame = 90;
  const textAppearFrame = 70;

  // 缓动函数
  const easeInOut = Easing.inOut(Easing.cubic);

  // 全局淡入
  const mainOpacity = interpolate(frame, [0, enterDuration], [0, 1], {
    easing: easeInOut,
    extrapolateRight: "clamp",
  });

  // 标题闪烁与出现逻辑
  const ceilingOpacity = interpolate(
    frame,
    [textAppearFrame, textAppearFrame + 10],
    [0, 1],
    {
      easing: easeInOut,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  let ceilingColor = "#EF4444"; // Error/Warning color
  if (frame >= textAppearFrame && frame < textAppearFrame + 30) {
    const isFlash = Math.floor(frame / 4) % 2 === 0;
    ceilingColor = isFlash ? "#EF4444" : "#FFFFFF";
  }

  // 列表项数据
  const bullets = ["企业扩张速度 > 专家培养速度", "传统模式失效"];

  // 天平倾斜动画 (左侧重，右侧轻 -> 逆时针旋转)
  const tipSpring = spring({
    frame: frame - scaleTipFrame,
    fps,
    config: { damping: 14, stiffness: 90 },
  });
  const beamRotation = interpolate(tipSpring, [0, 1], [0, -18]);

  // 图表淡入与上浮
  const diagramOpacity = interpolate(
    frame,
    [40, 60],
    [0, 1],
    {
      easing: easeInOut,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );
  const diagramY = interpolate(
    frame,
    [40, 60],
    [40, 0],
    {
      easing: easeInOut,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0F1729",
        padding: "100px 120px",
        boxSizing: "border-box",
        opacity: mainOpacity,
      }}
    >
      {/* 标题区域 */}
      <div style={{ position: "absolute", top: 100, left: 120 }}>
        <h1
          style={{
            fontFamily: "Inter",
            fontSize: 64,
            fontWeight: 700,
            color: "#FFFFFF",
            margin: 0,
            letterSpacing: "-0.02em",
          }}
        >
          靠人决策 ={" "}
          <span style={{ color: ceilingColor, opacity: ceilingOpacity }}>
            生产力天花板
          </span>
        </h1>
      </div>

      {/* 内容列表区域 */}
      <div
        style={{
          position: "absolute",
          top: 240,
          left: 120,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {bullets.map((text, index) => {
          const delay = 30 + index * stagger;
          const itemOpacity = interpolate(
            frame,
            [delay, delay + enterDuration],
            [0, 1],
            {
              easing: easeInOut,
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }
          );
          const itemX = interpolate(
            frame,
            [delay, delay + enterDuration],
            [-30, 0],
            {
              easing: easeInOut,
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }
          );

          return (
            <div
              key={index}
              style={{
                display: "flex",
                alignItems: "center",
                marginBottom: 24,
                opacity: itemOpacity,
                transform: `translateX(${itemX}px)`,
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
                style={{ marginRight: 16 }}
              >
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
              <span
                style={{
                  fontFamily: "Inter",
                  fontSize: 28,
                  fontWeight: 400,
                  color: "#E2E8F0",
                }}
              >
                {text}
              </span>
            </div>
          );
        })}
      </div>

      {/* 右侧天平图示区域 */}
      <div
        style={{
          position: "absolute",
          top: 220,
          right: 120,
          width: 800,
          height: 700,
          opacity: diagramOpacity,
          transform: `translateY(${diagramY}px)`,
        }}
      >
        <svg width="100%" height="100%" viewBox="0 0 800 700">
          {/* 天平底座 */}
          <path
            d="M360 600 L440 600 L400 250 Z"
            fill="#1E293B"
            stroke="#334155"
            strokeWidth="4"
            strokeLinejoin="round"
          />
          <circle cx="400" cy="250" r="12" fill="#3B82F6" />

          {/* 旋转的横梁及托盘组 */}
          <g transform={`rotate(${beamRotation}, 400, 250)`}>
            {/* 横梁 */}
            <line
              x1="150"
              y1="250"
              x2="650"
              y2="250"
              stroke="#94A3B8"
              strokeWidth="10"
              strokeLinecap="round"
            />
            <circle cx="150" cy="250" r="8" fill="#3B82F6" />
            <circle cx="650" cy="250" r="8" fill="#3B82F6" />

            {/* 左侧托盘 (企业扩张速度 - 重) */}
            <g
              transform={`translate(150, 250) rotate(${-beamRotation}) translate(-150, -250)`}
            >
              {/* 吊绳 */}
              <line x1="150" y1="250" x2="90" y2="420" stroke="#94A3B8" strokeWidth="3" />
              <line x1="150" y1="250" x2="210" y2="420" stroke="#94A3B8" strokeWidth="3" />
              {/* 托盘底 */}
              <path
                d="M70 420 Q150 460 230 420 Z"
                fill="#1E293B"
                stroke="#334155"
                strokeWidth="4"
              />
              {/* 重物方块 */}
              <rect
                x="90"
                y="300"
                width="120"
                height="120"
                rx="12"
                fill="#1E293B"
                stroke="#EF4444"
                strokeWidth="4"
              />
              <text
                x="150"
                y="350"
                fill="#E2E8F0"
                fontSize="22"
                fontFamily="Inter"
                fontWeight="700"
                textAnchor="middle"
                dominantBaseline="central"
              >
                企业
              </text>
              <text
                x="150"
                y="380"
                fill="#E2E8F0"
                fontSize="22"
                fontFamily="Inter"
                fontWeight="700"
                textAnchor="middle"
                dominantBaseline="central"
              >
                扩张速度
              </text>
            </g>

            {/* 右侧托盘 (专家培养速度 - 轻) */}
            <g
              transform={`translate(650, 250) rotate(${-beamRotation}) translate(-650, -250)`}
            >
              {/* 吊绳 */}
              <line x1="650" y1="250" x2="590" y2="420" stroke="#94A3B8" strokeWidth="3" />
              <line x1="650" y1="250" x2="710" y2="420" stroke="#94A3B8" strokeWidth="3" />
              {/* 托盘底 */}
              <path
                d="M570 420 Q650 460 730 420 Z"
                fill="#1E293B"
                stroke="#334155"
                strokeWidth="4"
              />
              {/* 轻物方块 */}
              <rect
                x="600"
                y="350"
                width="100"
                height="70"
                rx="12"
                fill="#1E293B"
                stroke="#3B82F6"
                strokeWidth="4"
              />
              <text
                x="650"
                y="375"
                fill="#E2E8F0"
                fontSize="18"
                fontFamily="Inter"
                fontWeight="400"
                textAnchor="middle"
                dominantBaseline="central"
              >
                专家
              </text>
              <text
                x="650"
                y="400"
                fill="#E2E8F0"
                fontSize="18"
                fontFamily="Inter"
                fontWeight="400"
                textAnchor="middle"
                dominantBaseline="central"
              >
                培养速度
              </text>
            </g>
          </g>
        </svg>
      </div>
    </AbsoluteFill>
  );
};