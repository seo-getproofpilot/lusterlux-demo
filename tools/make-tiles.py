#!/usr/bin/env python3
"""Category tiles built from LusterLux's own white-background studio photography.

The tiles used to be moody in-context shots, which made the top of the site read
dark. These crop the actual products out of their studio plates and set them on a
warm off-white ground, so the category row merchandises the line instead.
"""
import io, os, urllib.request
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "assets", "tiles")
RAW  = os.path.join(ROOT, "tools", "_raw")
# 16:9. .ctile-hit crops to 16/9 and the mega tile to 4/3, so the product is
# sized to sit inside the narrower 4:3 centre crop and survive both.
W, H = 1200, 675
BG   = (247, 246, 242)               # --bg

# category key -> (product handle, image index)
TILES = {
  "wash-waterless": ("foam-wash-system-1",          0),   # cannon + bottles
  "interior":       ("complete-interior-system-1",  0),   # sprays, brush, towels
  "towels-tools":   ("luxgun-pressure-washer-gun",  0),   # gun + colour-coded nozzles
  "kits-systems":   ("complete-detail-system-1",    0),
  "beyond-the-car": ("fairway-finish-system",       0),   # golf cart kit
  "wheels-tires":   ("tire-care-system-1",          0),
}

def fetch(handle, idx):
    cache = os.path.join(RAW, f"_tile_{handle}_{idx}")
    for ext in (".png", ".jpg"):
        if os.path.exists(cache + ext):
            return Image.open(cache + ext)
    url = f"https://lusterluxauto.com/products/{handle}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    import json
    p = json.load(urllib.request.urlopen(req, timeout=30))["product"]
    src = p["images"][idx]["src"].split("?")[0]
    ext = os.path.splitext(src)[1] or ".jpg"
    data = urllib.request.urlopen(
        urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
    open(cache + ext, "wb").write(data)
    return Image.open(io.BytesIO(data))

def content_box(im, tol=14):
    """Bounding box of the product against its near-white studio sweep."""
    g = im.convert("RGB")
    bg = Image.new("RGB", g.size, g.getpixel((2, 2)))
    diff = ImageChops.difference(g, bg).convert("L").point(lambda v: 255 if v > tol else 0)
    return diff.getbbox()

os.makedirs(OUT, exist_ok=True)
for key, (handle, idx) in TILES.items():
    im = fetch(handle, idx).convert("RGB")
    box = content_box(im)
    if box:
        pad = int(max(im.size) * 0.035)
        box = (max(0, box[0] - pad), max(0, box[1] - pad),
               min(im.width, box[2] + pad), min(im.height, box[3] + pad))
        im = im.crop(box)
    # fit the product inside the tile, leaving breathing room, on the warm ground
    canvas = Image.new("RGB", (W, H), BG)
    fit = im.copy(); fit.thumbnail((int(W * 0.42), int(H * 0.82)), Image.LANCZOS)
    canvas.paste(fit, ((W - fit.width) // 2, (H - fit.height) // 2))
    canvas.save(os.path.join(OUT, f"{key}.webp"), "WEBP", quality=88, method=6)
    print(f"  {key:16s} <- {handle}[{idx}]  crop={im.size} -> {fit.size}")
print("tiles written to assets/tiles/")
