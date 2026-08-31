#!/usr/bin/env python3
"""Square tiles for the Instagram strip, cropped from LusterLux's own photos.

Instagram, TikTok and Facebook all serve login-walled shells to unauthenticated
requests, so their actual posts and reels cannot be fetched. This builds the
profile's *shape* out of the owner photography we already have, with every tile
linking straight to the real profile. Nothing here claims to be a specific post,
and no follower or view counts are invented.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "tools", "_raw")
OUT  = os.path.join(ROOT, "assets", "ig")
S    = 620

# file -> vertical bias of the crop (0 = top, .5 = centre, 1 = bottom)
TILES = [
  ("IMG_9095_dddf0040-8491-4a47-9311-e981763631f3.jpg", .50),  # foam wash
  ("IMG_6876.jpg",                                      .50),  # Porsche wheel
  ("IMG_0927.jpg",                                      .50),  # ceramic, green car
  ("IMG_4677.jpg",                                      .50),  # 720S foamed
  ("IMG_0813.jpg",                                      .50),  # carbon wheel interior
  ("IMG_7130.jpg",                                      .50),  # golf cart
  ("IMG_6881.jpg",                                      .50),  # tire dressing
  ("IMG_0873_faea6b48-ce36-43c9-b4f1-84d2a5d82b35.jpg", .50),  # pearl hood
  ("IMG_7083_1.jpg",                                    .50),  # marine
]

os.makedirs(OUT, exist_ok=True)
for i, (fn, bias) in enumerate(TILES, 1):
    src = os.path.join(RAW, fn)
    if not os.path.exists(src):
        print(f"  !! missing {fn}"); continue
    im = Image.open(src).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top  = int((h - side) * bias)
    im = im.crop((left, top, left + side, top + side)).resize((S, S), Image.LANCZOS)
    out = os.path.join(OUT, f"ig-{i:02d}.webp")
    im.save(out, "WEBP", quality=84, method=6)
    print(f"  ig-{i:02d}.webp  <- {fn[:44]}")
print(f"{len(TILES)} tiles -> assets/ig/")
