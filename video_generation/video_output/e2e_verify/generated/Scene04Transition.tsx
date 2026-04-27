import React, { useMemo } from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
  Easing,
} from "remotion";

// 风格配置常量
const COLORS = {
  background: "#0F1729",
  primary: "#FFFFFF",
  secondary: "#94A3B8",
  accent: "#3B82F6",
  text: "#E2E8F0",
};

const TYPOGRAPHY = {
  titleFont: "Inter",
  titleSize: 64,
  titleWeight: 700,
  codeFont: "JetBrains Mono",
  codeSize: 22,
};

const ANIMATIONS = {
  enterDuration: 20,
};

// 生成固定的随机代码雨数据，避免渲染不一致
const CODE_SNIPPETS = [
  "function()", "=>", "const", "let", "return", "import", "from", "{}", "[]", 
  "class", "extends", "super()", "this.", "async", "await", "Promise", 
  "console.log", "if", "else", "true", "false", "null", "undefined", "@Decorator"
];

const generateRainData = (width: number) => {
  const columns = 40;
  const data = [];
  for (let i = 0; i < columns; i++) {
    const snippets = [];
    for (let j = 0; j < 15; j++) {
      // 使用伪随机确保每次渲染一致
      const index = (i * 7 + j * 13) % CODE_SNIPPETS.length;
      snippets.push(CODE_SNIPPETS[index]);
    }
    data.push({
      x: (width / columns) * i,
      speed: 1.5 + ((i * 3) % 4), // 1.5 到 4.5 的速度
      offset: (i * 150) % 1080, // 初始 Y 偏移
      text: snippets.join("\n\n"),
      opacity: 0.03 + ((i * 7) % 5) * 0.01, // 0.03 到 0.07 的透明度
    });
  }
  return data;
};

export const Scene04Transition: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // 动画时间轴定义
  const enterStart = 0;
  const enterEnd = ANIMATIONS.enterDuration;
  const holdDuration = 90; // 停留 3 秒 (3 * 30fps)
  const scatterStart = enterEnd + holdDuration; // 110
  const scatterEnd = scatterStart + 40; // 150

  // 1. 背景代码雨动画
  const rainData = useMemo(() => generateRainData(width), [width]);

  // 2. 主文本入场动画 (淡入 + 轻微放大)
  const containerOpacity = interpolate(
    frame,
    [enterStart, enterEnd],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const containerScale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
    durationInFrames: enterEnd,
  });
  // 将 spring 的 0->1 映射到 0.8->1
  const mappedScale = 0.8 + containerScale * 0.2;

  // 3. 主文本内容与散开动画
  const text = "基础语法与 @ 语法糖";
  const chars = text.split("");
  const centerIndex = Math.floor(chars.length / 2);

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.background, overflow: "hidden" }}>
      
      {/* 背景：隐约落下的代码字符雨 */}
      <AbsoluteFill>
        {rainData.map((col, i) => {
          const yPos = ((frame * col.speed + col.offset) % (height + 1000)) - 1000;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: col.x,
                top: yPos,
                color: COLORS.accent,
                opacity: col.opacity,
                fontFamily: TYPOGRAPHY.codeFont,
                fontSize: TYPOGRAPHY.codeSize * 0.8,
                whiteSpace: "pre-wrap",
                lineHeight: 2,
                textAlign: "center",
                width: width / 40,
              }}
            >
              {col.text}
            </div>
          );
        })}
      </AbsoluteFill>

      {/* 前景：居中文字 */}
      <AbsoluteFill
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          flexDirection: "row",
          opacity: containerOpacity,
          transform: `scale(${mappedScale})`,
        }}
      >
        {chars.map((char, index) => {
          // 计算散开动画参数
          const distanceFromCenter = index - centerIndex;
          // 决定向左还是向右散开，中心字符随机偏向一侧
          const direction = distanceFromCenter < 0 ? -1 : distanceFromCenter > 0 ? 1 : (index % 2 === 0 ? -1 : 1);
          
          // 散开的 X 轴位移
          const scatterX = interpolate(
            frame,
            [scatterStart, scatterEnd],
            [0, direction * (500 + Math.abs(distanceFromCenter) * 100)],
            { 
              easing: Easing.inOut(Easing.cubic),
              extrapolateLeft: "clamp", 
              extrapolateRight: "clamp" 
            }
          );

          // 散开时的 Y 轴轻微偏移和旋转，增加动感
          const scatterY = interpolate(
            frame,
            [scatterStart, scatterEnd],
            [0, (index % 3 - 1) * 50],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );

          const scatterRotate = interpolate(
            frame,
            [scatterStart, scatterEnd],
            [0, direction * (10 + Math.abs(distanceFromCenter) * 5)],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );

          // 散开时的透明度
          const charOpacity = interpolate(
            frame,
            [scatterStart + 10, scatterEnd],
            [1, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );

          // 颜色高亮 @ 符号
          const isAccent = char === "@";
          const color = isAccent ? COLORS.accent : COLORS.primary;

          return (
            <span
              key={index}
              style={{
                display: "inline-block",
                fontFamily: TYPOGRAPHY.titleFont,
                fontSize: TYPOGRAPHY.titleSize,
                fontWeight: TYPOGRAPHY.titleWeight,
                color: color,
                whiteSpace: "pre",
                opacity: charOpacity,
                transform: `translate(${scatterX}px, ${scatterY}px) rotate(${scatterRotate}deg)`,
                textShadow: isAccent ? `0 0 20px ${COLORS.accent}80` : "none",
              }}
            >
              {char}
            </span>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};