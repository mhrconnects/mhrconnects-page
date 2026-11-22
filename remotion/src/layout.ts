import { useVideoConfig } from "remotion";

/** Layout metrics for vertical Shorts (1080x1920) and landscape long-form (1920x1080). */
export const useLayout = () => {
  const { width, height } = useVideoConfig();
  const landscape = width > height;
  return landscape
    ? {
        landscape,
        stageTop: 70,
        stageHeight: 800,
        stageX: 160,
        contentMaxWidth: 1500,
        contentScale: 0.82,
        captionTop: 905,
        captionSize: 54,
        captionStroke: 9,
        handleBottom: 30,
      }
    : {
        landscape,
        stageTop: 170,
        stageHeight: 1060,
        stageX: 80,
        contentMaxWidth: width - 160,
        contentScale: 1,
        captionTop: 1290,
        captionSize: 86,
        captionStroke: 12,
        handleBottom: 250,
      };
};
