import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
} from "remotion";

export const Scene09Content: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // 动画计算
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 20], [-20, 0], {
    extrapolateRight: "clamp",
  });

  // 列表项交错动画
  const bullets = [
    {
      text: (
        <>
          问题：丢失 <span style={styles.inlineCode}>__name__</span> 和{" "}
          <span style={styles.inlineCode}>__doc__</span>
        </>
      ),
    },
    {
      text: (
        <>
          解决：导入 <span style={styles.inlineCode}>functools.wraps</span>
        </>
      ),
    },
    {
      text: (
        <>
          用法：在 wrapper 上添加{" "}
          <span style={styles.inlineCode}>@wraps(func)</span>
        </>
      ),
    },
  ];

  // 左侧错误情况动画 (60帧开始)
  const leftBoxOpacity = interpolate(frame, [60, 80], [0, 1], {
    extrapolateRight: "clamp",
  });
  const leftBoxY = interpolate(frame, [60, 80], [40, 0], {
    extrapolateRight: "clamp",
  });
  const redXScale = spring({
    frame: frame - 90,
    fps,
    config: { damping: 12, stiffness: 150 },
  });

  // 右侧正确情况动画 (150帧开始)
  const rightBoxOpacity = interpolate(frame, [150, 170], [0, 1], {
    extrapolateRight: "clamp",
  });
  const rightBoxX = interpolate(frame, [150, 170], [60, 0], {
    extrapolateRight: "clamp",
  });
  const shieldScale = spring({
    frame: frame - 180,
    fps,
    config: { damping: 12, stiffness: 120 },
  });
  const shieldGlow = interpolate(frame, [180, 210], [0, 1], {
    extrapolateRight: "clamp",
  });
  const checkScale = spring({
    frame: frame - 210,
    fps,
    config: { damping: 12, stiffness: 150 },
  });

  // 进度条
  const progressWidth = interpolate(frame, [0, durationInFrames], [0, 1920], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0F1729" }}>
      <div style={styles.container}>
        {/* 标题 */}
        <div
          style={{
            ...styles.title,
            opacity: titleOpacity,
            transform: `translateY(${titleY}px)`,
          }}
        >
          守护元信息：functools.wraps
        </div>

        {/* 内容区 */}
        <div style={styles.contentWrapper}>
          {/* 左侧：要点列表 */}
          <div style={styles.leftPanel}>
            {bullets.map((bullet, i) => {
              const delay = i * 6 + 20;
              const opacity = interpolate(
                frame,
                [delay, delay + 15],
                [0, 1],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
              );
              const x = interpolate(
                frame,
                [delay, delay + 15],
                [-30, 0],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
              );

              return (
                <div
                  key={i}
                  style={{
                    ...styles.bulletItem,
                    opacity,
                    transform: `translateX(${x}px)`,
                  }}
                >
                  <svg
                    width={14}
                    height={14}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#3B82F6"
                    style={styles.bulletIcon}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  <div style={styles.bulletText}>{bullet.text}</div>
                </div>
              );
            })}
          </div>

          {/* 右侧：对比图示 */}
          <div style={styles.rightPanel}>
            {/* 左侧对比框 (未使用 wraps) */}
            <div
              style={{
                ...styles.diagramBox,
                opacity: leftBoxOpacity,
                transform: `translateY(${leftBoxY}px)`,
              }}
            >
              <div style={styles.boxTitle}>未使用 wraps</div>
              <div style={styles.metaDataCard}>
                <div style={styles.metaRow}>
                  <span style={styles.metaKey}>__name__:</span>
                  <span style={styles.metaValueError}>"wrapper"</span>
                </div>
                <div style={styles.metaRow}>
                  <span style={styles.metaKey}>__doc__:</span>
                  <span style={styles.metaValueError}>None</span>
                </div>
              </div>
              {/* 红叉 */}
              <div
                style={{
                  ...styles.iconOverlay,
                  transform: `translate(-50%, -50%) scale(${redXScale})`,
                  opacity: redXScale > 0 ? 1 : 0,
                }}
              >
                <svg
                  width={80}
                  height={80}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#EF4444"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
            </div>

            {/* 右侧对比框 (使用 wraps) */}
            <div
              style={{
                ...styles.diagramBox,
                opacity: rightBoxOpacity,
                transform: `translateX(${rightBoxX}px)`,
                borderColor: `rgba(59, 130, 246, ${shieldGlow * 0.5})`,
                boxShadow: `0 0 ${shieldGlow * 30}px rgba(59, 130, 246, 0.2)`,
              }}
            >
              <div style={styles.boxTitle}>使用 @wraps(func)</div>
              
              {/* 盾牌背景 */}
              <div
                style={{
                  ...styles.shieldBackground,
                  transform: `translate(-50%, -50%) scale(${shieldScale})`,
                  opacity: shieldScale > 0 ? 0.15 + shieldGlow * 0.1 : 0,
                }}
              >
                <svg
                  width={160}
                  height={160}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#3B82F6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
                  />
                </svg>
              </div>

              <div style={{...styles.metaDataCard, borderColor: '#3B82F6'}}>
                <div style={styles.metaRow}>
                  <span style={styles.metaKey}>__name__:</span>
                  <span style={styles.metaValueSuccess}>"original_func"</span>
                </div>
                <div style={styles.metaRow}>
                  <span style={styles.metaKey}>__doc__:</span>
                  <span style={styles.metaValueSuccess}>"This is a doc..."</span>
                </div>
              </div>
              
              {/* 绿勾 */}
              <div
                style={{
                  ...styles.iconOverlay,
                  transform: `translate(-50%, -50%) scale(${checkScale})`,
                  opacity: checkScale > 0 ? 1 : 0,
                  marginTop: 60,
                  marginLeft: 60,
                }}
              >
                <div style={styles.checkCircle}>
                  <svg
                    width={40}
                    height={40}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#22C55E"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={4}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 底部进度条 */}
      <div style={styles.progressBarContainer}>
        <div style={{ ...styles.progressBar, width: progressWidth }} />
      </div>
    </AbsoluteFill>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: 1920,
    height: 1080,
    padding: "100px 120px",
    boxSizing: "border-box",
    display: "flex",
    flexDirection: "column",
  },
  title: {
    fontFamily: "Inter",
    fontSize: 64,
    fontWeight: 700,
    color: "#FFFFFF",
    marginBottom: 80,
  },
  contentWrapper: {
    display: "flex",
    flexDirection: "row",
    flex: 1,
    gap: 60,
  },
  leftPanel: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: 40,
    marginTop: 20,
  },
  bulletItem: {
    display: "flex",
    alignItems: "flex-start",
    position: "relative",
    paddingLeft: 36,
  },
  bulletIcon: {
    position: "absolute",
    left: 0,
    top: 10,
  },
  bulletText: {
    fontFamily: "Inter",
    fontSize: 28,
    fontWeight: 400,
    color: "#E2E8F0",
    lineHeight: 1.5,
  },
  inlineCode: {
    fontFamily: "JetBrains Mono",
    fontSize: 22,
    color: "#3B82F6",
    backgroundColor: "rgba(59, 130, 246, 0.15)",
    padding: "4px 10px",
    borderRadius: 6,
    margin: "0 6px",
  },
  rightPanel: {
    flex: 1.2,
    display: "flex",
    flexDirection: "row",
    gap: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  diagramBox: {
    width: 360,
    height: 420,
    backgroundColor: "#1E293B",
    border: "2px solid #334155",
    borderRadius: 12,
    padding: 32,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    position: "relative",
    boxSizing: "border-box",
  },
  boxTitle: {
    fontFamily: "Inter",
    fontSize: 24,
    fontWeight: 700,
    color: "#94A3B8",
    marginBottom: 40,
    textAlign: "center",
  },
  metaDataCard: {
    width: "100%",
    backgroundColor: "#0F1729",
    border: "1px solid #334155",
    borderRadius: 8,
    padding: 24,
    display: "flex",
    flexDirection: "column",
    gap: 20,
    zIndex: 2,
    boxSizing: "border-box",
  },
  metaRow: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  metaKey: {
    fontFamily: "JetBrains Mono",
    fontSize: 20,
    color: "#94A3B8",
  },
  metaValueError: {
    fontFamily: "JetBrains Mono",
    fontSize: 22,
    color: "#EF4444",
  },
  metaValueSuccess: {
    fontFamily: "JetBrains Mono",
    fontSize: 22,
    color: "#22C55E",
  },
  iconOverlay: {
    position: "absolute",
    top: "50%",
    left: "50%",
    zIndex: 10,
  },
  shieldBackground: {
    position: "absolute",
    top: "55%",
    left: "50%",
    zIndex: 1,
    filter: "drop-shadow(0 0 20px rgba(59, 130, 246, 0.8))",
  },
  checkCircle: {
    width: 64,
    height: 64,
    backgroundColor: "#1E293B",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: "4px solid #22C55E",
    boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
  },
  progressBarContainer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    width: 1920,
    height: 3,
    backgroundColor: "rgba(255,255,255,0.1)",
  },
  progressBar: {
    height: "100%",
    backgroundColor: "#3B82F6",
  },
};