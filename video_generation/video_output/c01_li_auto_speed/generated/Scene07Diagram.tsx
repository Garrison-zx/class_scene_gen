import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
} from "remotion";

export const Scene07Diagram: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 风格配置常量
  const colors = {
    background: "#0F1729",
    primary: "#FFFFFF",
    secondary: "#94A3B8",
    accent: "#3B82F6",
    text: "#E2E8F0",
    textSecondary: "#94A3B8",
    error: "#EF4444",
  };

  const typography = {
    titleFont: "Inter",
    titleSize: 64,
    titleWeight: 700,
    bodyFont: "Inter",
    bodySize: 28,
    bodyWeight: 400,
  };

  const layout = {
    padding: { top: 100, bottom: 100, left: 120, right: 120 },
  };

  const diagramConfig = {
    nodeBackground: "#1E293B",
    nodeBorder: "#334155",
    nodeBorderRadius: 12,
    labelColor: "#E2E8F0",
  };

  // 全局入场动画
  const globalOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 标题动画
  const titleY = interpolate(frame, [0, 20], [-30, 0], {
    extrapolateRight: "clamp",
  });

  // 左侧折线图动画
  const chartOpacity = interpolate(frame, [20, 40], [0, 1], {
    extrapolateRight: "clamp",
  });
  const lineDrawProgress = spring({
    frame: frame - 40,
    fps,
    config: { damping: 200, stiffness: 40 },
  });
  const pathLength = 1200;
  const dashOffset = pathLength * (1 - lineDrawProgress);

  // 右侧孤岛节点配置
  const nodes = [
    { id: "供应商 A", x: 80, y: 60 },
    { id: "供应商 B", x: 480, y: 80 },
    { id: "供应商 C", x: 40, y: 320 },
    { id: "供应商 D", x: 500, y: 360 },
    { id: "供应商 E", x: 280, y: 200 },
  ];

  // 底部核心知识点
  const keyPoints = [
    "技师培养跟不上扩张",
    "供应链数据孤岛",
    "追溯耗时过长",
  ];

  // 节点闪烁计算函数
  const getNodeFlash = (index: number) => {
    const startFrame = 80 + index * 15;
    if (frame < startFrame) return 0;
    // 每 90 帧循环一次闪烁
    const cycleFrame = (frame - startFrame) % 90;
    return interpolate(cycleFrame, [0, 15, 30], [0, 1, 0], {
      extrapolateRight: "clamp",
    });
  };

  return (
    <AbsoluteFill style={{ backgroundColor: colors.background, fontFamily: typography.titleFont }}>
      {/* 标题区域 */}
      <div
        style={{
          position: "absolute",
          top: layout.padding.top,
          left: layout.padding.left,
          opacity: globalOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: typography.titleSize,
            fontWeight: typography.titleWeight,
            color: colors.primary,
          }}
        >
          售后孤岛与追溯难题
        </h1>
      </div>

      {/* 内容区域：双图表对比 */}
      <div
        style={{
          position: "absolute",
          top: 240,
          left: layout.padding.left,
          right: layout.padding.right,
          height: 550,
          display: "flex",
          justifyContent: "space-between",
          opacity: chartOpacity,
        }}
      >
        {/* 左侧：折线图 */}
        <div
          style={{
            width: 750,
            height: "100%",
            position: "relative",
            backgroundColor: "rgba(30, 41, 59, 0.3)",
            borderRadius: 16,
            border: `1px solid ${diagramConfig.nodeBorder}`,
            padding: 30,
            boxSizing: "border-box",
          }}
        >
          <div style={{ color: colors.primary, fontSize: 24, fontWeight: 600, marginBottom: 20 }}>
            门店扩张 vs 技师培养
          </div>
          <svg width="100%" height="420" style={{ overflow: "visible" }}>
            {/* 网格线 */}
            {[100, 200, 300].map((y) => (
              <line
                key={y}
                x1="50"
                y1={y}
                x2="650"
                y2={y}
                stroke={colors.secondary}
                strokeOpacity={0.1}
                strokeWidth="1"
              />
            ))}
            
            {/* 坐标轴 */}
            <path
              d="M 50 50 L 50 400 L 650 400"
              fill="none"
              stroke={colors.secondary}
              strokeWidth="2"
            />
            
            {/* 门店扩张曲线 (陡峭) */}
            <path
              d="M 50 400 C 300 400, 400 50, 650 50"
              fill="none"
              stroke={colors.accent}
              strokeWidth="4"
              strokeDasharray={pathLength}
              strokeDashoffset={dashOffset}
              strokeLinecap="round"
            />
            
            {/* 技师培养曲线 (平缓) */}
            <path
              d="M 50 400 C 300 400, 400 320, 650 300"
              fill="none"
              stroke={colors.secondary}
              strokeWidth="4"
              strokeDasharray={pathLength}
              strokeDashoffset={dashOffset}
              strokeLinecap="round"
            />
          </svg>

          {/* 图例 */}
          <div style={{ display: "flex", gap: 30, position: "absolute", bottom: 30, left: 80 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 16, height: 4, backgroundColor: colors.accent, borderRadius: 2 }} />
              <span style={{ color: colors.textSecondary, fontSize: 20 }}>门店数量</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 16, height: 4, backgroundColor: colors.secondary, borderRadius: 2 }} />
              <span style={{ color: colors.textSecondary, fontSize: 20 }}>资深技师</span>
            </div>
          </div>
        </div>

        {/* 右侧：关系图 (数据孤岛) */}
        <div
          style={{
            width: 750,
            height: "100%",
            position: "relative",
            backgroundColor: "rgba(30, 41, 59, 0.3)",
            borderRadius: 16,
            border: `1px solid ${diagramConfig.nodeBorder}`,
            padding: 30,
            boxSizing: "border-box",
          }}
        >
          <div style={{ color: colors.primary, fontSize: 24, fontWeight: 600, marginBottom: 20 }}>
            供应链数据孤岛
          </div>
          <div style={{ position: "relative", width: "100%", height: 420 }}>
            {nodes.map((node, i) => {
              const nodeOpacity = interpolate(frame, [40 + i * 5, 60 + i * 5], [0, 1], {
                extrapolateRight: "clamp",
              });
              const nodeScale = spring({
                frame: frame - (40 + i * 5),
                fps,
                config: { damping: 15 },
              });
              const flashIntensity = getNodeFlash(i);
              
              // 闪烁时的边框和阴影颜色
              const currentBorderColor = `rgba(${interpolate(flashIntensity, [0, 1], [51, 239])}, ${interpolate(flashIntensity, [0, 1], [65, 68])}, ${interpolate(flashIntensity, [0, 1], [85, 68])}, 1)`; // 从 #334155 到 #EF4444
              
              return (
                <div
                  key={node.id}
                  style={{
                    position: "absolute",
                    left: node.x,
                    top: node.y,
                    width: 160,
                    height: 64,
                    backgroundColor: diagramConfig.nodeBackground,
                    border: `2px solid ${currentBorderColor}`,
                    borderRadius: diagramConfig.nodeBorderRadius,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: diagramConfig.labelColor,
                    fontSize: 22,
                    fontWeight: 500,
                    opacity: nodeOpacity,
                    transform: `scale(${nodeScale})`,
                    boxShadow: flashIntensity > 0 ? `0 0 20px rgba(239, 68, 68, ${flashIntensity * 0.6})` : "none",
                    transition: "box-shadow 0.1s, border-color 0.1s",
                  }}
                >
                  {node.id}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 底部核心知识点 */}
      <div
        style={{
          position: "absolute",
          bottom: layout.padding.bottom,
          left: layout.padding.left,
          right: layout.padding.right,
          display: "flex",
          justifyContent: "space-around",
          alignItems: "center",
        }}
      >
        {keyPoints.map((point, i) => {
          const delay = 100 + i * 15;
          const pointOpacity = interpolate(frame, [delay, delay + 20], [0, 1], {
            extrapolateRight: "clamp",
          });
          const pointY = interpolate(frame, [delay, delay + 20], [20, 0], {
            extrapolateRight: "clamp",
          });

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                opacity: pointOpacity,
                transform: `translateY(${pointY}px)`,
              }}
            >
              {/* Bullet Icon */}
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                style={{ marginRight: 16 }}
              >
                <path
                  d="M9 18L15 12L9 6"
                  stroke={colors.accent}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span
                style={{
                  color: colors.text,
                  fontSize: typography.bodySize,
                  fontWeight: typography.bodyWeight,
                }}
              >
                {point}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};