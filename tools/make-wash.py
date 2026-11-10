#!/usr/bin/env python3
"""Hero wash plates: their own McLaren 720S, foamed and rinsed.

IMG_4677 and IMG_4704 are the same car in the same bay from almost the same
spot — one blanketed in LuxFoam, one rinsed. That registered pair is what makes
a real scroll-driven rinse possible instead of a cross-fade.

The camera drifted ~40px between frames, so the rinsed plate is aligned to the
foamed one on the static wall above the car before anything is differenced. The
foam alpha is then just where the foamed plate is brighter than the rinsed one,
normalised and softened. The shader dissolves that alpha away on scroll.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "tools", "_raw")
OUT  = os.path.join(ROOT, "assets", "wash")
FOAM, CLEAN = "IMG_4677.jpg", "IMG_4704.jpg"
WIDTHS = {"d": 1920, "m": 1080}

os.makedirs(OUT, exist_ok=True)
a = Image.open(os.path.join(RAW, FOAM)).convert("RGB")
b = Image.open(os.path.join(RAW, CLEAN)).convert("RGB")
W, H = a.size

ga = np.asarray(a.convert("L"), dtype=np.float32)
gb = np.asarray(b.convert("L"), dtype=np.float32)

# Align on the wall strip above the car; the car and ground both change.
y0, y1, x0, x1 = 40, 300, 200, 2000
ref = ga[y0:y1, x0:x1]
best = (1e18, 0, 0)
for dy in range(-60, 61):
    for dx in range(-30, 31):
        cand = gb[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        if cand.shape != ref.shape:
            continue
        v = float(np.abs(ref - cand).mean())
        if v < best[0]:
            best = (v, dx, dy)
_, dx, dy = best
print(f"  align dx={dx} dy={dy}")

shifted = Image.new("RGB", (W, H))
shifted.paste(b, (-dx, -dy))
cx0, cy0 = max(0, -dx) + 8, max(0, -dy) + 8
cx1, cy1 = W - max(0, dx) - 8, H - max(0, dy) - 8
a_c = a.crop((cx0, cy0, cx1, cy1))
b_c = shifted.crop((cx0, cy0, cx1, cy1))

d = np.clip(np.asarray(a_c.convert("L"), np.float32)
            - np.asarray(b_c.convert("L"), np.float32), 0, 255)
alpha = np.clip((d - 18) / 110.0, 0, 1) ** 0.85
am = Image.fromarray(np.uint8(alpha * 255)).filter(ImageFilter.GaussianBlur(2.0))

for tag, w in WIDTHS.items():
    h = round(a_c.height * w / a_c.width)
    a_c.resize((w, h), Image.LANCZOS).save(f"{OUT}/foam-{tag}.webp", "WEBP", quality=86, method=6)
    b_c.resize((w, h), Image.LANCZOS).save(f"{OUT}/clean-{tag}.webp", "WEBP", quality=88, method=6)
    am.resize((w, h), Image.LANCZOS).save(f"{OUT}/alpha-{tag}.webp", "WEBP", quality=90, method=6)
    print(f"  {tag}: {w}x{h}")

print(f"crop {a_c.size} -> assets/wash/")
