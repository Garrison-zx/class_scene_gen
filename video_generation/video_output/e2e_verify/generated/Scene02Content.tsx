import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
} from "remotion";

export const Scene02Content: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleX = interpolate(frame, [0, 20], [-100, 0], {
    extrapolateRight: "clamp",
  });
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const bullets = [
    "本质：高阶函数",
    "机制：接收函数，返回新函数",
    "优势：不修改原函数代码，实现功能增强",
  ];

  const iconContainerDelay = 40;
  const gearScale = spring({
    frame: Math.max(0, frame - iconContainerDelay),
    fps,
    config: { damping: 15, stiffness: 150 },
  });
  const gearRotation = frame * 0.8;

  const shieldDelay = iconContainerDelay + 30;
  const shieldScale = spring({
    frame: Math.max(0, frame - shieldDelay),
    fps,
    config: { damping: 12, stiffness: 120 },
  });
  const shieldGlow = interpolate(
    frame,
    [shieldDelay + 10, shieldDelay + 40],
    [0, 25],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0F1729",
        padding: "100px 120px",
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <div
        style={{
          transform: `translateX(${titleX}px)`,
          opacity: titleOpacity,
          fontSize: 64,
          fontWeight: 700,
          color: "#FFFFFF",
          lineHeight: 1.5,
        }}
      >
        什么是装饰器？
      </div>

      <div
        style={{
          display: "flex",
          flex: 1,
          marginTop: 80,
          maxWidth: 1400,
        }}
      >
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            gap: 48,
            marginLeft: 36,
          }}
        >
          {bullets.map((bullet, i) => {
            const delay = 20 + i * 24;
            const itemOpacity = interpolate(
              frame,
              [delay, delay + 20],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            const itemX = interpolate(frame, [delay, delay + 20], [-50, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });

            return (
              <div
                key={i}
                style={{
                  opacity: itemOpacity,
                  transform: `translateX(${itemX}px)`,
                  display: "flex",
                  alignItems: "center",
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
                  style={{ marginRight: 16, flexShrink: 0 }}
                >
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
                <span
                  style={{
                    fontSize: 28,
                    fontWeight: 400,
                    color: "#E2E8F0",
                    lineHeight: 1.5,
                  }}
                >
                  {bullet}
                </span>
              </div>
            );
          })}
        </div>

        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              transform: `scale(${gearScale}) rotate(${gearRotation}deg)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg
              width="240"
              height="240"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#94A3B8"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ opacity: 0.8 }}
            >
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </div>

          <div
            style={{
              position: "absolute",
              transform: `scale(${shieldScale})`,
              filter: `drop-shadow(0 0 ${shieldGlow}px rgba(59, 130, 246, 0.9))`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg
              width="140"
              height="140"
              viewBox="0 0 24 24"
              fill="rgba(59, 130, 246, 0.15)"
              stroke="#3B82F6"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};