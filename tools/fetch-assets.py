#!/usr/bin/env python3
"""
LusterLux demo — asset pipeline.

Pulls the studio product photos from the live Shopify CDN, cuts the white
studio background to transparent (edge-seeded flood fill, NOT a global white
threshold -- the labels are chrome and a global threshold punches holes
straight through the highlights), feathers the edge, trims, and writes
optimized WebP into assets/products/.

Also samples each bottle's dominant chroma so every product can carry its own
accent colour in the UI, and writes a contact sheet for eyeballing the cutouts.

    python3 tools/fetch-assets.py            # everything
    python3 tools/fetch-assets.py luxpro     # one key
"""
import io, json, os, re, sys, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDN  = "https://cdn.shopify.com/s/files/1/1038/9435/1953/files/"
RAW  = os.path.join(ROOT, "tools", "_raw")
OUT  = os.path.join(ROOT, "assets", "products")
SCENE= os.path.join(ROOT, "assets", "scene")
UA   = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# key -> (cdn filename, flood threshold)
# threshold is tuned per file: low where the product itself has white/chrome
# areas that a greedy fill would eat (LuxFoam's white cap, the towels).
CUTOUTS = {
  "luxpro":     ("Luxpro_professional_web_photo.png?v=1784783191", 26),
  "ceramicx":   ("CeramicX_professional_web_photo.png?v=1784783338", 26),
  "luxquick":   ("LuxQuick_professioanl_web_photo.png?v=1784783506", 26),
  "restorx":    ("RestorX_professioanl_web_photo.png?v=1784783615", 26),
  "tirevenom":  ("Tirevenom_professioanl_web_photo.png?v=1784783871", 26),
  "vanillaember":("Vanilla_Ember_professioanl_web_photo.png?v=1784784201", 26),
  "newcarember":("NewCarEmber_professioanl_photo.png?v=1784784286", 26),
  "luxfoam":    ("LuxFoam_profesisoanl_web_photo_146c43f4-07f3-4355-934b-11e594a68804.png?v=1784784505", 14),
  "wheelassassin":("LuxWheelAssassin_professional_website_photo.png?v=1784784893", 26),
  "xfresh":     ("Xfresh_professioanl_web_photo.png?v=1784785055", 26),
  "interiorx":  ("InteriorX_wesbite_professioanl_photo.png?v=1784785160", 26),
  "birdielux":  ("BirdieLux_professioanl_Web_photo.png?v=1784785342", 26),
  "luxcannon":  ("LuxCannonn_professioanl_web_photo.png?v=1784785939", 78),
  "luxbucket":  ("LuxBucket_professioanl_wbe_photo.png?v=1784786248", 58),
  "luxgun":     ("lucgun_professioaNL_WEB_PHOTOT.png?v=1784786661", 92),
  "edgelesslux":("EdgelessLux_3_pack_professioanl_web_photo.png?v=1784788170", 135),
  "microlux":   ("m_MicroLux_5_pack_microfibers_professioanl_photo.png?v=1784787946", 135),
}

# lifestyle / scene plates -- no cutout, just optimized
# Scene plates carry two sizes. A 1650x2200 source decodes to ~14MB of bitmap;
# eleven of those on one page is 160MB of decoded image, which is what makes a long
# page stutter. Full size is only for the full-bleed hero and closing plate -- every
# card and tier tile gets the -sm variant.
SCENE_SM = 900
PROD_SM = 460

SCENES = {
  # real owner/shop photography from the product galleries -- no burned-in badges
  "hero-foam":   "IMG_9095_dddf0040-8491-4a47-9311-e981763631f3.jpg",
  "hero-hood":   "IMG_9123.jpg",
  "hero-wheel":  "IMG_6876.jpg",
  "nano-hood":   "IMG_0873_faea6b48-ce36-43c9-b4f1-84d2a5d82b35.jpg",
  "wheel-caliper":"IMG_6881.jpg",
  "ceramic":     "IMG_0927.jpg",
  "interior":    "IMG_0813.jpg",
  "cart":        "IMG_7130.jpg",
  "marine":      "IMG_7083_1.jpg",
  # the LuxFoam drag comparison -- same car, same framing, foamed vs rinsed
  "towels":      "IMG_1086.jpg",
  "kitshot":     "IMG_9420_-_Edited.png",
  # in-use plates: each hero product photographed on the surface it works on.
  # These sit behind the cut-out bottle in the homepage showcases.
  "use-luxpro":        "IMG_0873_faea6b48-ce36-43c9-b4f1-84d2a5d82b35.jpg",
  "use-ceramicx":      "IMG_0927.jpg",
  "use-luxfoam":       "IMG_1217.jpg",
  "use-wheelassassin": "IMG_6876.jpg",
  "use-tirevenom":     "IMG_6881.jpg",
  "use-interiorx":     "IMG_0813.jpg",
  "founders":    "Why_LusterLux_Pic_2_4d044122-f8d8-46f7-b4fd-4280dfae3f9a.jpg",
  "founders-2":  "IMG_8358.jpg",
  "ba-before":   "IMG_4677.jpg",
  "ba-after":    "IMG_4704.jpg",
}

# plates that are ever shown full-bleed, so they keep a large variant too
SCENE_FULL = {"hero-foam", "hero-wheel", "hero-hood", "nano-hood", "wheel-caliper",
              "ba-before", "ba-after", "interior", "cart", "towels", "kitshot", "marine", "ceramic", "founders", "founders-2"}

# --- everything else in the catalog, so the shop grid is one cohesive dark set.
# Photoroom_* files already ship with an alpha channel; the pipeline detects that
# and skips the flood entirely rather than re-cutting an already-clean edge.
REST = {
  "the-luxcap-limited-supply":            ("Photoroom_20260513_221653.png", 60),
  "lux-t":                                ("Photoroom_20260507_171522.png", 60),
  "lux-brush-interior-brush":             ("intbrush.jpg", 95),
  "the-platinum-system":                  ("IMG_9420_-_Edited.png", 60),
  "ultimate-wash-system-1":               ("UltimateWashSytemKitphoto.jpg", 118),
  "rim-and-tire-system-kit-1":            ("RimandTireSystemKitphoto.jpg", 60),
  "foam-wash-system-1":                   ("FoamWashSystemKitphoto.jpg", 60),
  "complete-interior-system-1":           ("CompleterInteriorSystemKitphoto.jpg", 60),
  "paint-care-system-1":                  ("PaintCareStyemKitphoto.jpg", 60),
  "complete-detail-system-1":             ("CompleteDetailSystemKitphoto.jpg", 60),
  "interior-restoration-system-1":        ("InteriorRestorationSystemKitphoto.jpg", 60),
  "tire-care-system-1":                   ("TireCareSystemKitphoto.jpg", 60),
  "waterless-wash-system-1":              ("waterlesswahssystemkitphoto.jpg", 60),
  "dual-scent-system-1":                  ("DualScentSystem.jpg", 60),
  "fairway-finish-system":                ("Photoroom_20260515_020435_2.jpg", 60),
  "trail-foam-coming-soon":               ("comingsoonfortopofcatpage.png", 60),
  "foamx-sprayer-electric-sprayer":       ("85A628DF-E2C6-4A5C-9BDE-30639BDEA1AF_1.png", 60),
  "lux-sprayer-pump-sprayer":             ("CE19E50C-0D00-4398-BCBD-34D8737AFA72_1.png", 60),
  "luxmit-wash-mit":                      ("Photoroom_20260412_173525.png", 60),
  "2-pack-xpad-applicator-pad":           ("apppoad.jpg", 72),
  "luxbug-bug-and-tar-remover-sponge":    ("bugthing.jpg", 60),
  "towel-tantrum-kit":                    ("Photoroom_20260513_190021.jpg", 60),
  "luxtowel-drying-towel":                ("Dryingtowel_1.jpg", 60),
  "2-pack-luxwindow":                     ("Photoroom_20260507_094321.png", 60),
  "lux-tire-brush":                       ("tirebbrush.jpg", 150),
  "lux-wheel-brush":                      ("wheelbrush.png", 60),
}
CUTOUTS.update(REST)

KEY = (255, 0, 255)  # flood marker colour, guaranteed absent from the photos

# Products whose studio shadow leaves bright pockets the flood cannot reach --
# the shadow's own dark core walls them off. These get a second pass that grows
# the background through *neutral + bright* pixels only, so it eats the shadow
# without touching a coloured bottle or a lime towel.
HALO = {"luxcannon", "luxgun", "edgelesslux", "microlux"}

# Products with studio white fully enclosed by the product itself (the pressure
# washer's trigger guard). Nothing connected can reach it, so knock out anything
# that is still near-paper-white and neutral.
# key -> luminance above which a still-opaque neutral pixel is treated as studio
# white walled off from the border. Default 236; lowered per item where the product
# itself is dark enough that a looser cut is safe.
HOLES = {"luxgun": 236, "lux-brush-interior-brush": 200, "lux-tire-brush": 165,
         "2-pack-xpad-applicator-pad": 236, "lux-wheel-brush": 200, "luxcannon": 236}
HALO |= set(REST)


def grow_halo(im, alpha):
    """Extend the background through connected neutral-bright pixels."""
    r, g, b = im.split()
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    bright  = mx.point(lambda v: 255 if v > 188 else 0)
    neutral = ImageChops.difference(mx, mn).point(lambda v: 255 if v < 30 else 0)
    band = ImageChops.multiply(bright, neutral)          # candidate shadow/studio

    seed = ImageChops.multiply(ImageChops.invert(alpha), band)
    for _ in range(90):
        grown = ImageChops.multiply(seed.filter(ImageFilter.MaxFilter(9)), band)
        if ImageChops.difference(grown, seed).getbbox() is None:
            break
        seed = grown
    return ImageChops.multiply(alpha, ImageChops.invert(seed))


def fetch(name, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    safe = re.sub(r"[^\w.-]", "_", name.split("?")[0])
    path = os.path.join(dest_dir, safe)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    url = CDN + name
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


# Single-object products where the studio shadow leaves a detached bright wedge
# the flood cannot reach. Keeping only the dominant blob removes it outright.
TRIM = {"lux-tire-brush", "lux-brush-interior-brush", "2-pack-xpad-applicator-pad",
        "lux-wheel-brush", "luxcannon"}


def keep_main(alpha, frac=0.10):
    """Drop every opaque blob smaller than `frac` of the largest one."""
    m = alpha.point(lambda v: 255 if v > 128 else 0)
    w, h = m.size
    px = m.load()
    label, areas = 1, {}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if px[x, y] == 255 and label < 250:
                ImageDraw.floodfill(m, (x, y), label)
                label += 1
    hist = m.histogram()
    for i in range(1, label):
        areas[i] = hist[i]
    if not areas:
        return alpha
    biggest = max(areas.values())
    drop = [i for i, a in areas.items() if a < biggest * frac]
    if not drop:
        return alpha
    dropset = set(drop)
    keep = m.point(lambda v: 0 if v in dropset else 255)
    return ImageChops.multiply(alpha, keep)


def cutout(path, thresh, halo=False, holes=False, trim=False):
    """Edge-seeded flood fill from the border, then erode + feather the alpha."""
    raw = Image.open(path)
    if raw.mode in ("RGBA", "LA", "P") and "transparency" in raw.info or raw.mode in ("RGBA", "LA"):
        rgba = raw.convert("RGBA")
        if rgba.getchannel("A").getextrema()[0] < 250:      # genuinely cut already
            rgba.thumbnail((900, 900), Image.LANCZOS)
            bb = rgba.getchannel("A").getbbox()
            return rgba.crop(bb) if bb else rgba
    im = raw.convert("RGB")
    w, h = im.size
    work = im.copy()

    # seed from every border pixel that is still background-coloured. Seeding the
    # whole border (not just the corners) survives a bottle that runs off an edge.
    step = max(1, min(w, h) // 60)
    seeds = []
    for x in range(0, w, step):
        seeds += [(x, 0), (x, h - 1)]
    for y in range(0, h, step):
        seeds += [(0, y), (w - 1, y)]
    for s in seeds:
        if work.getpixel(s) != KEY:
            ImageDraw.floodfill(work, s, KEY, thresh=thresh)

    # alpha: 0 where the fill reached, 255 everywhere else
    r, g, b = work.split()
    hit = ImageChops.multiply(
        ImageChops.multiply(r.point(lambda v: 255 if v > 250 else 0),
                            g.point(lambda v: 255 if v < 5 else 0)),
        b.point(lambda v: 255 if v > 250 else 0))
    alpha = ImageChops.invert(hit)
    if halo:
        alpha = grow_halo(im, alpha)
    if holes:
        hi = holes if isinstance(holes, int) else 236
        r2, g2, b2 = im.split()
        mx = ImageChops.lighter(ImageChops.lighter(r2, g2), b2)
        mn = ImageChops.darker(ImageChops.darker(r2, g2), b2)
        white = ImageChops.multiply(mx.point(lambda v: 255 if v > hi else 0),
                                    ImageChops.difference(mx, mn).point(lambda v: 255 if v < 16 else 0))
        white = white.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
        alpha = ImageChops.multiply(alpha, ImageChops.invert(white))

    # erode 1px so no white studio fringe survives, then feather
    alpha = alpha.filter(ImageFilter.MinFilter(3))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))

    if trim:
        alpha = keep_main(alpha)

    im.putalpha(alpha)
    bbox = alpha.getbbox()
    if bbox:
        pad = 6
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(w, bbox[2] + pad), min(h, bbox[3] + pad))
        im = im.crop(bbox)
    im.thumbnail((900, 900), Image.LANCZOS)
    return im


def accent(im):
    """Dominant saturated colour of the cut-out product -> its UI accent."""
    small = im.convert("RGBA").resize((90, 90), Image.LANCZOS)
    buckets = {}
    for px in small.getdata():
        r, g, b, a = px
        if a < 200:
            continue
        mx, mn = max(r, g, b), min(r, g, b)
        if mx < 60 or mx - mn < 42:      # skip black plastic + neutral chrome
            continue
        k = (r // 26 * 26, g // 26 * 26, b // 26 * 26)
        buckets[k] = buckets.get(k, 0) + 1
    if not buckets:
        return "#84D019"
    best = max(buckets.items(), key=lambda kv: kv[1])[0]
    # lift toward a usable UI colour: keep hue, push value/chroma up
    r, g, b = [min(255, int(c * 1.16) + 26) for c in best]
    return "#%02x%02x%02x" % (r, g, b)


def main():
    only = set(a.lower() for a in sys.argv[1:])
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCENE, exist_ok=True)
    accents, sheet = {}, []

    for key, (fname, th) in CUTOUTS.items():
        if only and key not in only:
            continue
        src = fetch(fname, RAW)
        im = cutout(src, th, key in HALO, HOLES.get(key, False), key in TRIM)
        im.save(os.path.join(OUT, key + ".webp"), "WEBP", quality=90, method=6)
        # grid-sized variant -- the shop page shows 43 of these at ~275px, and decoding
        # 43 full-size cutouts is what makes that page stutter on the way down
        sm = im.copy(); sm.thumbnail((PROD_SM, PROD_SM), Image.LANCZOS)
        sm.save(os.path.join(OUT, key + "-sm.webp"), "WEBP", quality=86, method=6)
        accents[key] = accent(im)
        sheet.append((key, im))
        print(f"  {key:<14} {im.size[0]}x{im.size[1]}  acc {accents[key]}")

    if not only:
        for key, fname in SCENES.items():
            src = fetch(fname + "?width=2400", RAW)
            base = Image.open(src).convert("RGB")
            if key in SCENE_FULL:
                im = base.copy()
                im.thumbnail((1500, 1500), Image.LANCZOS)
                im.save(os.path.join(SCENE, key + ".webp"), "WEBP", quality=80, method=6)
                print(f"  scene/{key:<14} {im.size[0]}x{im.size[1]}")
            sm = base.copy()
            sm.thumbnail((SCENE_SM, SCENE_SM), Image.LANCZOS)
            sm.save(os.path.join(SCENE, key + "-sm.webp"), "WEBP", quality=78, method=6)
            print(f"  scene/{key + '-sm':<14} {sm.size[0]}x{sm.size[1]}")

    # contact sheet on a dark ground -- this is how the bottles will actually sit
    if sheet:
        cw, ch, cols = 240, 300, 6
        rows = (len(sheet) + cols - 1) // cols
        cs = Image.new("RGB", (cols * cw, rows * ch), (8, 9, 14))
        d = ImageDraw.Draw(cs)
        for i, (k, im) in enumerate(sheet):
            t = im.copy(); t.thumbnail((cw - 24, ch - 54), Image.LANCZOS)
            x, y = (i % cols) * cw, (i // cols) * ch
            cs.paste(t, (x + (cw - t.size[0]) // 2, y + 16), t)
            d.text((x + 10, y + ch - 26), k, fill=(140, 145, 155))
        cs.save(os.path.join(ROOT, "tools", "_contact.png"))
        print("\ncontact sheet -> tools/_contact.png")

    print("\nACCENTS =", json.dumps(accents, indent=2))


if __name__ == "__main__":
    main()
