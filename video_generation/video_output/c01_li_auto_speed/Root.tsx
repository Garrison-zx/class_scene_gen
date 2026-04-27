/**
 * Root.tsx — 自动生成，请勿手动编辑。
 *
 * 由 video_generation pipeline Stage 3 (assembler) 生成。
 * 注册所有场景为独立 Composition，并提供完整视频 Composition。
 */

import { Audio, Composition, Sequence, staticFile } from "remotion";
import { Scene01Title } from "./generated/Scene01Title";
import { Scene02Content } from "./generated/Scene02Content";
import { Scene03Transition } from "./generated/Scene03Transition";
import { Scene04Diagram } from "./generated/Scene04Diagram";
import { Scene05Content } from "./generated/Scene05Content";
import { Scene06Transition } from "./generated/Scene06Transition";
import { Scene07Diagram } from "./generated/Scene07Diagram";
import { Scene08Summary } from "./generated/Scene08Summary";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* ── 独立场景（方便单独预览） ── */}
      <Composition
        id="scene-01"
        component={Scene01Title}
        durationInFrames={286}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-02"
        component={Scene02Content}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-03"
        component={Scene03Transition}
        durationInFrames={262}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-04"
        component={Scene04Diagram}
        durationInFrames={363}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-05"
        component={Scene05Content}
        durationInFrames={450}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-06"
        component={Scene06Transition}
        durationInFrames={195}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-07"
        component={Scene07Diagram}
        durationInFrames={480}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="scene-08"
        component={Scene08Summary}
        durationInFrames={450}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* ── 完整视频（所有场景串联） ── */}
      <Composition
        id="full-video"
        component={FullVideo}
        durationInFrames={2846}
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
        <Sequence from={0} durationInFrames={286}>
          <Scene01Title />
          <Audio src={staticFile("audio/scene_01.mp3")} />
        </Sequence>
        <Sequence from={286} durationInFrames={360}>
          <Scene02Content />
          <Audio src={staticFile("audio/scene_02.mp3")} />
        </Sequence>
        <Sequence from={646} durationInFrames={262}>
          <Scene03Transition />
          <Audio src={staticFile("audio/scene_03.mp3")} />
        </Sequence>
        <Sequence from={908} durationInFrames={363}>
          <Scene04Diagram />
          <Audio src={staticFile("audio/scene_04.mp3")} />
        </Sequence>
        <Sequence from={1271} durationInFrames={450}>
          <Scene05Content />
          <Audio src={staticFile("audio/scene_05.mp3")} />
        </Sequence>
        <Sequence from={1721} durationInFrames={195}>
          <Scene06Transition />
          <Audio src={staticFile("audio/scene_06.mp3")} />
        </Sequence>
        <Sequence from={1916} durationInFrames={480}>
          <Scene07Diagram />
          <Audio src={staticFile("audio/scene_07.mp3")} />
        </Sequence>
        <Sequence from={2396} durationInFrames={450}>
          <Scene08Summary />
          <Audio src={staticFile("audio/scene_08.mp3")} />
        </Sequence>
    </>
  );
};
