#!/usr/bin/env python3
"""Portrait reel tiles for the Instagram strip, from LusterLux's own photos.

Instagram, TikTok and Facebook all serve login-walled shells to unauthenticated
requests, their storefront runs no feed app, and there is no video anywhere on
their Shopify CDN — so real posts and reels cannot be embedded. This builds the
profile's shape out of the owner photography we already have, with every tile
linking to the real account. Nothing claims to be a specific post and no metrics
are invented.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "tools", "_raw")
OUT  = os.path.join(ROOT, "assets", "ig")
W, H = 720, 1280                      # 9:16, the reel frame

# (source, vertical bias 0=top .5=centre 1=bottom, caption)
TILES = [
  ("IMG_9095_dddf0040-8491-4a47-9311-e981763631f3.jpg", .45, "Foam day in the driveway"),
  ("IMG_6876.jpg",                                      .50, "Brake dust never stood a chance"),
  ("IMG_0927.jpg",                                      .45, "Ceramic gloss on a green machine"),
  ("IMG_1217.jpg",                                      .50, "LuxFoam, top to bottom"),
  ("IMG_0813.jpg",                                      .50, "Interiors get the same care"),
  ("IMG_7130.jpg",                                      .50, "Carts clean up too"),
  ("IMG_6881.jpg",                                      .50, "Sidewalls back to black"),
  ("IMG_7083_1.jpg",                                    .50, "Lake day prep"),
]

os.makedirs(OUT, exist_ok=True)
for old in os.listdir(OUT):
    os.remove(os.path.join(OUT, old))

for i, (fn, bias, cap) in enumerate(TILES, 1):
    src = os.path.join(RAW, fn)
    if not os.path.exists(src):
        print(f"  !! missing {fn}"); continue
    im = Image.open(src).convert("RGB")
    w, h = im.size
    target = W / H
    if w / h > target:                      # too wide: trim the sides
        nw = int(h * target); left = (w - nw) // 2; box = (left, 0, left + nw, h)
    else:                                   # too tall: trim top/bottom by bias
        nh = int(w / target); top = int((h - nh) * bias); box = (0, top, w, top + nh)
    im = im.crop(box).resize((W, H), Image.LANCZOS)
    im.save(os.path.join(OUT, f"ig-{i:02d}.webp"), "WEBP", quality=82, method=6)
    print(f"  ig-{i:02d}.webp  {box[2]-box[0]}x{box[3]-box[1]}  <- {fn[:38]}")
print(f"{len(TILES)} reel tiles -> assets/ig/")
