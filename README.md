# mhrconnects-page

A 3D explainer for **MHR Connects**, built with Three.js.

- `index.html`: the 36-second animated 3D explainer. It plays in the browser and loops. Serve the folder with any static server, for example `npx serve .`, because ES modules don't load from `file://`.
- `video/mhr-connects-explainer.mp4`: the same explainer rendered to video (1920×1080, 30 fps, about 38 s).
- `video/poster.jpg`: a still of the closing title card.

## Storyboard

| Time | Scene | On-screen copy |
|------|-------|----------------|
| 0–6s | Title: nodes fly in and form a ring | MHR Connects · Connect · Collaborate · Grow |
| 6–12s | The problem: nodes scatter and turn grey | People, ideas and opportunities are scattered. |
| 12–18s | Connect: nodes gather into a sphere around a hub and links draw in | MHR Connects brings everyone into one network. |
| 18–24s | Collaborate: pulses travel along the links | Share, match and work together in real time. |
| 24–30s | Grow: new amber nodes join and the camera pulls back | Your network expands, and so does your impact. |
| 30–36s | Closing card | MHR Connects · Get started |

The copy is placeholder text. Edit it in the overlay `<div>`s in `index.html`. Scene timings are in `renderAt()`.

## Re-rendering the MP4

```bash
node tools/render-frames.js . /tmp/frames 30      # needs Playwright + Chromium
ffmpeg -framerate 30 -i /tmp/frames/f%05d.jpg -c:v libx264 -crf 20 -pix_fmt yuv420p video/mhr-connects-explainer.mp4
```
