// Fonts are bundled from npm (@fontsource) so rendering never needs to download them.
import "@fontsource/inter/400.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/800.css";
import "@fontsource/inter/900.css";
import "@fontsource/space-grotesk/500.css";
import "@fontsource/space-grotesk/700.css";
import { continueRender, delayRender } from "remotion";

if (typeof document !== "undefined") {
  const handle = delayRender("Loading fonts");
  Promise.all(
    ["400 40px Inter", "600 40px Inter", "800 40px Inter", "900 40px Inter", "700 40px 'Space Grotesk'", "500 40px 'Space Grotesk'"].map(
      (f) => document.fonts.load(f),
    ),
  )
    .catch(() => undefined)
    .then(() => continueRender(handle));
}
