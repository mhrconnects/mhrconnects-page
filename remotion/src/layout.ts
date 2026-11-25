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
        contentScale: 0.76,
        captionTop: 935,
        captionSize: 50,
        captionStroke: 9,
        handleBottom: 30,
      }
    : {
        landscape,
        // Kept inside the TikTok/Reels/Shorts safe zone: clear of the top tabs,
        // the right-hand buttons and the bottom caption/username area.
        stageTop: 240,
        stageHeight: 960,
        stageX: 90,
        contentMaxWidth: width - 180,
        contentScale: 0.86,
        captionTop: 1215,
        captionSize: 62,
        captionStroke: 9,
        handleBottom: 250,
      };
};
