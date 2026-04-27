/**
 * Root.tsx — 自动生成，请勿手动编辑。
 *
 * 由 video_generation pipeline Stage 3 (assembler) 生成。
 * 注册所有场景为独立 Composition，并提供完整视频 Composition。
 */

import { Composition, Sequence } from "remotion";
import { Scene01Title } from "./generated/Scene01Title";
import { Scene02Content } from "./generated/Scene02Content";
import { Scene03Diagram } from "./generated/Scene03Diagram";
import { Scene04Transition } from "./generated/Scene04Transition";
import { Scene05Code } from "./generated/Scene05Code";
import { Scene06Content } from "./generated/Scene06Content";
import { Scene07Transition } from "./generated/Scene07Transition";
import { Scene08Code } from "./generated/Scene08Code";
import { Scene09Content } from "./generated/Scene09Content";
import { Scene10Summary } from "./generated/Scene10Summary";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* ── 独立场景（方便单独预览） ── */}
      <Composition
        id="scene-01"
        component={Scene01Title}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-02"
        component={Scene02Content}
        durationInFrames={450}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-03"
        component={Scene03Diagram}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-04"
        component={Scene04Transition}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-05"
        component={Scene05Code}
        durationInFrames={540}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-06"
        component={Scene06Content}
        durationInFrames={420}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-07"
        component={Scene07Transition}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-08"
        component={Scene08Code}
        durationInFrames={600}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-09"
        component={Scene09Content}
        durationInFrames={450}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-10"
        component={Scene10Summary}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* ── 完整视频（所有场景串联） ── */}
      <Composition
        id="full-video"
        component={FullVideo}
        durationInFrames={3900}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};

const FullVideo: React.FC = () => {
  return (
    <>
        <Sequence from={0} durationInFrames={240}>
          <Scene01Title />
        </Sequence>
        <Sequence from={240} durationInFrames={450}>
          <Scene02Content />
        </Sequence>
        <Sequence from={690} durationInFrames={360}>
          <Scene03Diagram />
        </Sequence>
        <Sequence from={1050} durationInFrames={240}>
          <Scene04Transition />
        </Sequence>
        <Sequence from={1290} durationInFrames={540}>
          <Scene05Code />
        </Sequence>
        <Sequence from={1830} durationInFrames={420}>
          <Scene06Content />
        </Sequence>
        <Sequence from={2250} durationInFrames={240}>
          <Scene07Transition />
        </Sequence>
        <Sequence from={2490} durationInFrames={600}>
          <Scene08Code />
        </Sequence>
        <Sequence from={3090} durationInFrames={450}>
          <Scene09Content />
        </Sequence>
        <Sequence from={3540} durationInFrames={360}>
          <Scene10Summary />
        </Sequence>
    </>
  );
};
