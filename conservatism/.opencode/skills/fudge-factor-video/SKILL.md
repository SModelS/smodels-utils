---
name: fudge-factor-video
description: Use when the user asks to create a video from fudge factor / pvalue PNG files (e.g. pvalues*_norm.png). Generates an mp4 slideshow with hard cuts between frames.
---

# Fudge Factor Video Clip Maker

Creates a video clip from `pvalues*_norm.png` files sorted by fudge factor value.

## Workflow

1. List all `pvalues*_norm.png` files in the current directory.
2. Extract the numeric fudge factor from each filename and sort **descending** (highest first, e.g. 1.0 → 0.03).
3. Generate a `concat.txt` for ffmpeg's concat demuxer:
   - Each entry is an absolute path + `duration 1` (1 second per frame).
   - Repeat the last file entry **without** a duration line so ffmpeg holds the final frame.
4. Encode with ffmpeg:
   ```
   ffmpeg -y -f concat -safe 0 -i concat.txt -vf "fps=30" \
     -c:v libx264 -pix_fmt yuv420p -crf 18 pvalues_video.mp4
   ```
5. Clean up `concat.txt`.

## Result

- Output: `pvalues_video.mp4`
- Each frame displays for 1 second with hard cuts (no transitions).
- ~37 seconds for the default 36 fudge factors (1.0 down to 0.03).

## Customization

- **Smooth crossfade transitions**: use Python + PIL to generate intermediate blended frames at 30 fps, then encode the frame sequence with `ffmpeg -framerate 30 -i %05d.png`.
- **Different hold duration**: change the `duration` value in concat.txt.
- **Different fps**: change `-vf "fps=30"` to the desired frame rate.
