# Reel video goes here

Drop MP4s named to match the tiles in `tools/build-site.py` → `IG_TILES`:

    ig-01.mp4  ig-02.mp4  ig-03.mp4  …

The build detects them automatically. Any tile with a matching file renders a
`<video muted loop playsinline preload="none">` with the existing WebP as its
poster, plays on hover, and gains an unmute button. Tiles without a file stay
a still image — no dead controls.

Encode roughly:

    ffmpeg -i source.mov -vf "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280" \
           -c:v libx264 -crf 26 -preset slow -movflags +faststart -an -t 8 ig-01.mp4

`-an` strips audio. Keep audio only if the unmute button should do something.
