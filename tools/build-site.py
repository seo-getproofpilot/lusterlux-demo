#!/usr/bin/env python3
"""
LusterLux — static site generator.

Reads data/catalog.json and writes the full site tree. Routes follow Shopify's
native shape (/products/<handle>/, /collections/<category>/) because that is what
the real store uses -- and what adamspolishes.com, the reference model, uses.

    python3 tools/build-catalog.py && python3 tools/build-site.py
"""
import json, os, re, shutil, html, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "data", "catalog.json")))
P    = DATA["products"]
CATS = DATA["cats"]
WORLDS = DATA["worlds"]
GROUPS = DATA["groups"]
SUBS   = DATA["subs"]
WORLD_KEYS = {w["k"] for w in WORLDS}
V    = "75"                                   # cache-bust, bump on every build
STORE = "https://lusterluxauto.com"
SITE  = "https://lusterluxauto.com"           # canonical host — canonicals/schema always point here
# Deploy prefix. Empty for the real domain; set LL_BASE=/lusterlux-demo for a
# GitHub Pages project site, which serves from a subpath.
BASE  = os.environ.get("LL_BASE", "").rstrip("/")
FREE  = DATA["meta"]["freeShipping"]

_gs = importlib.util.spec_from_file_location("guides", os.path.join(ROOT, "tools", "guides.py"))
_gm = importlib.util.module_from_spec(_gs); _gs.loader.exec_module(_gm)
GUIDES = _gm.GUIDES

by_handle = {p["h"]: p for p in P}

IG = "https://www.instagram.com/lusterluxauto/"
TT = "https://www.tiktok.com/@lusterluxauto"
YT = "https://www.youtube.com/@lusterluxauto"
FB = "https://www.facebook.com/lusterluxauto"

# Instagram strip. Their posts and reels are not fetchable — every platform
# login-walls unauthenticated requests — so these are their own photographs
# shaped like the profile, each opening the real account.
IG_TILES = [
  ("ig-01", "Foam wash in the driveway",            True),
  ("ig-02", "Wheel cleaner on a Porsche wheel",     False),
  ("ig-03", "Ceramic spray on a green performance car", True),
  ("ig-04", "A 720S blanketed in LuxFoam",          True),
  ("ig-05", "Interior cleaner on a carbon wheel",   False),
  ("ig-06", "Golf cart cleaned with BirdieLux",     True),
  ("ig-07", "Tire dressing on a finished wheel",    False),
  ("ig-08", "Waterless wash on a pearl hood",       False),
  ("ig-09", "Marine wash on the lake",              True),
]

def ig_grid():
    reel = ('<svg class="ig-reel" viewBox="0 0 24 24" fill="none" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M3 8h18M8.5 3 11 8M15 3l2.5 5"/>'
            '<rect x="3" y="3" width="18" height="18" rx="4"/>'
            '<path d="m10.5 12.2 4 2.1-4 2.1Z" fill="currentColor"/></svg>')
    return "".join(
      f'<a class="ig-tile" href="{IG}" target="_blank" rel="noopener" '
      f'aria-label="{alt} — open LusterLux on Instagram">'
      f'<img src="/assets/ig/{k}.webp?v={V}" alt="{alt}" loading="lazy" decoding="async" />'
      + (reel if is_reel else "") + '</a>'
      for k, alt, is_reel in IG_TILES)
def cat_name(k):
    for c in CATS:
        if c["k"] == k: return c["t"]
    return k
def cat_desc(k):
    for c in CATS:
        if c["k"] == k: return c["d"]
    return ""
def in_cat(k):
    return [p for p in P if p["cat"] == k or k in p.get("also", [])]
def in_world(k):
    return [p for p in P if k in p.get("worlds", [])]
def prod_sub(p):
    """The subcategory a product lives in, falling back to its group."""
    return p.get("sub") or p.get("group") or "kits-systems"
def prod_sub_name(p):
    k = prod_sub(p)
    m = sub_meta(k)
    return m["t"] if m["t"] != k else group_meta(k)["t"]
def sub_meta(k):
    for s in SUBS:
        if s["k"] == k: return s
    return {"k": k, "t": k, "d": ""}
def in_sub(k):
    """Beyond-the-Car subs are the vehicle worlds, which are cross-listed."""
    if k in WORLD_KEYS: return in_world(k)
    return [p for p in P if p.get("sub") == k]
def in_group(k):
    if k == "kits-systems": return [p for p in P if p["cat"] == "kits-systems"]
    return [p for p in P if p.get("group") == k]
def group_meta(k):
    for g in GROUPS:
        if g["k"] == k: return g
    return {"k": k, "t": k, "d": "", "subs": []}
def world_name(k):
    for w in WORLDS:
        if w["k"] == k: return w["t"]
    return k

SHOP_CATS = [c for c in CATS if c["k"] != "merch"]
CAT_ACC = {"wash-waterless":"#6a4cf0","wheels-tires":"#c8763a","interior":"#d4a53c",
           "towels-tools":"#9aa4ae","beyond-the-car":"#8a76e8","kits-systems":"#84D019",
           "merch":"#9aa4ae"}


def worlds_links():
    return "".join(
      f'<a href="/collections/{w["k"]}/">{w["t"]}<b>{len(in_world(w["k"]))}</b></a>'
      for w in WORLDS)


def world_tiles(current=""):
    return "".join(
      f'<a class="wtile{" on" if w["k"]==current else ""}" href="/collections/{w["k"]}/">'
      f'<img src="/assets/tiles/world-{w["k"]}.webp?v={V}" alt="LusterLux detailing products for {plain(w["t"]).lower()}" loading="lazy" decoding="async" />'
      f'<span class="wtile-body"><b>{w["t"]}</b><em>{w["d"]}</em>'
      f'<i>{len(in_world(w["k"]))} products</i></span></a>' for w in WORLDS)


GROUP_TILE = {"exterior":"wash-waterless","interior":"interior","tools":"towels-tools",
              "kits-systems":"kits-systems","beyond-the-car":"beyond-the-car"}
GROUP_ACC  = {"exterior":"#6a4cf0","interior":"#d4a53c","tools":"#9aa4ae",
              "kits-systems":"#84D019","beyond-the-car":"#8a76e8"}

def cat_tiles():
    out = ""
    for g in GROUPS:
        subs = "".join(f'<a href="/collections/{sk}/">{sub_meta(sk)["t"]}</a>' for sk in g["subs"])
        out += (f'<div class="ctile" style="--acc:{GROUP_ACC[g["k"]]}">'
                f'<a class="ctile-hit" href="/collections/{g["k"]}/" aria-label="{plain(g["t"])}">'
                f'<img src="/assets/tiles/{GROUP_TILE[g["k"]]}.webp?v={V}" alt="LusterLux {plain(g["t"]).lower()} products" loading="lazy" decoding="async" /></a>'
                f'<div class="ctile-body"><a class="ctile-name" href="/collections/{g["k"]}/">{g["t"]}</a>'
                f'<i>{len(in_group(g["k"]))} products</i>'
                + (f'<nav class="ctile-subs">{subs}</nav>' if subs else '')
                + '</div></div>')
    return out


def stars_svg(n=5):
    star = ('<svg viewBox="0 0 24 24"><path d="m12 2 3 6.6 7 .8-5.2 4.8 1.4 7L12 17.8 5.8 21.2'
            'l1.4-7L2 9.4l7-.8L12 2Z"/></svg>')
    return star * n


def honeycomb(cols=None):
    """Photo mosaic. Flat-top hexes in vertically-offset columns; falls back to a
       plain grid below 1100px (see .hex-* in site.css). Wide-and-short by default —
       three tall columns ate a full screen of vertical space for decoration."""
    cols = cols or [[1, 2], [3, 4, 5], [6, 7], [8, 9, 10]]
    alts = ["A car mid foam wash", "A performance wheel and LusterLux wheel cleaner",
            "LuxPro on a pearl hood", "A McLaren blanketed in LuxFoam",
            "A carbon steering wheel being detailed", "A golf cart cleaned with BirdieLux",
            "The same McLaren rinsed clean", "CeramicX beside a green performance car",
            "LusterLux products beside a boat", "A dressed tire and wheel",
            "Foam clinging to a hood", "LusterLux microfiber towels"]
    out = ""
    for ci, col in enumerate(cols):
        cells = "".join(
          f'<span class="hex"><img src="/assets/hex/hex-{n:02d}.webp?v={V}" '
          f'alt="{esc(alts[n-1])}" loading="lazy" decoding="async" /></span>' for n in col)
        out += f'<div class="hex-col{" off" if ci % 2 else ""}">{cells}</div>'
    return out


def strip_items():
    bits = ["Free shipping over $45", "Made in the USA", "Safe on PPF, wraps &amp; ceramic",
            "5.00 &#9733; from 17 verified reviews", "Built by detailers, not a boardroom"]
    return "".join(f"<span>{b}</span>" for b in bits)

def esc(s): return html.escape(str(s), quote=True)
def plain(s):
    """Entity-decoded plain text, for <title>/meta where esc() runs again."""
    return html.unescape(re.sub("<[^>]+>", "", str(s)))
def money(n): return f"${n:,.2f}"

# ---------------------------------------------------------------- partials --
def head(title, desc, canonical, extra="", og_img="/assets/brand/og-card.jpg"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(plain(title))}</title>
<meta name="description" content="{esc(plain(desc))}" />
<link rel="canonical" href="{SITE}{canonical}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="LusterLux" />
<meta property="og:title" content="{esc(plain(title))}" />
<meta property="og:description" content="{esc(plain(desc))}" />
<meta property="og:url" content="{SITE}{canonical}" />
<meta property="og:image" content="{SITE}{og_img}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="theme-color" content="#05060a" />
<link rel="icon" href="/favicon.ico" sizes="any" />
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Cinzel:wght@400..900&family=Instrument+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
<script>document.documentElement.className+=" js";</script>
<link rel="stylesheet" href="/assets/site.css?v={V}" />
{extra}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""

def nav(active=""):
    items = [("/collections/", "Shop", "shop"),
             ("/pages/find-your-product/", "Find Your Product", "find"),
             ("/pages/nanofusion/", "NanoFusion", "nano"),
             ("/blogs/guides/", "Guides", "guides"),
             ("/pages/community/", "Community", "community")]
    links = ""
    for href, label, key in items:
        cur = ' aria-current="page"' if active == key else ""
        if key == "shop":
            cells = ""
            for g in GROUPS:
                subs = "".join(
                  f'<a href="/collections/{sk}/">{sub_meta(sk)["t"]}<b>{len(in_sub(sk))}</b></a>'
                  for sk in g["subs"])
                cells += (
                  f'<div class="mcell" style="--acc:{GROUP_ACC[g["k"]]}">'
                  f'<a class="mtile" href="/collections/{g["k"]}/">'
                  f'<img src="/assets/tiles/{GROUP_TILE[g["k"]]}.webp?v={V}" '
                  f'alt="LusterLux {plain(g["t"]).lower()} products" loading="lazy" decoding="async" />'
                  f'<i></i><span class="mtile-body"><b>{g["t"]}</b>'
                  f'<span>{len(in_group(g["k"]))} products</span></span></a>'
                  + (f'<div class="mcol-subs">{subs}</div>' if subs else '')
                  + '</div>')
            links += (f'<li class="has-mega"><a href="{href}"{cur}>{label}'
                      '<svg class="car" viewBox="0 0 24 24" fill="none" stroke-linecap="round" '
                      'stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg></a>'
                      f'<div class="mega"><div class="mega-grid">{cells}</div>'
                      '<div class="mega-foot"><p>New to this? '
                      '<a class="lime" href="/pages/find-your-product/">Answer two questions</a> '
                      'and we will name the bottle.</p>'
                      '<a class="btn btn-primary btn-sm" href="/collections/">Shop all'
                      '<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>'
                      '</div></div></li>')
        else:
            links += f'<li><a href="{href}"{cur}>{label}</a></li>'
    mob = ""
    for g in GROUPS:
        mob += f'<a href="/collections/{g["k"]}/">{g["t"]}<span>{len(in_group(g["k"]))}</span></a>'
        for sk in g["subs"]:
            mob += (f'<a class="msub" href="/collections/{sk}/">{sub_meta(sk)["t"]}'
                    f'<span>{len(in_sub(sk))}</span></a>')
    return f"""<header class="nav" id="nav">
  <div class="nav-in">
    <a class="brand" href="/" aria-label="LusterLux home">
      <img class="brand-mark" src="/assets/brand/lusterlux-mark-320.webp?v={V}" alt="" width="218" height="320" />
      <span class="brand-wm">LUSTER<i>LUX</i></span>
    </a>
    <nav aria-label="Primary"><ul class="nav-links">{links}</ul></nav>
    <div class="nav-actions">
      <button class="icon-btn" type="button" data-cart-open aria-label="Open cart">
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M6 7h12l-1.2 12.2a2 2 0 0 1-2 1.8H9.2a2 2 0 0 1-2-1.8Z"/><path d="M9 7V5.6A3 3 0 0 1 12 2.6a3 3 0 0 1 3 3V7"/></svg>
        <span class="cart-badge" data-cart-count hidden>0</span>
      </button>
      <button class="burger" id="burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mpanel">
        <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>
    </div>
  </div>
</header>
<div class="mpanel" id="mpanel">
  {mob}
  <a href="/pages/find-your-product/">Find Your Product</a>
  <a href="/pages/nanofusion/">NanoFusion</a>
  <a href="/blogs/guides/">Guides</a>
  <a href="/pages/community/">Community</a>
  <a href="/pages/about/">Our Story</a>
  <a class="btn btn-primary" href="/collections/">Shop all</a>
</div>
"""

def drawer():
    return f"""<div class="drawer" id="cartDrawer" aria-hidden="true" role="dialog" aria-label="Cart" aria-modal="true">
  <div class="drawer-scrim" id="cartScrim"></div>
  <aside class="drawer-panel">
    <header class="drawer-head">
      <h2>Your cart</h2>
      <button class="icon-btn" id="cartClose" type="button" aria-label="Close cart">
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>
      </button>
    </header>
    <p class="free-bar" id="cartFree"></p>
    <ul class="cart-lines" id="cartLines"></ul>
    <footer class="drawer-foot">
      <p class="sub"><span>Subtotal</span><b id="cartSub">$0.00</b></p>
      <p class="fine">Shipping and tax calculated at checkout. Free over {money(FREE)}.</p>
      <a class="btn btn-primary" id="cartCheckout" href="{STORE}/cart">Checkout
        <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      <a class="tlink" href="/cart/">View full cart</a>
    </footer>
  </aside>
</div>"""

def footer():
    shop = "".join(f'<li><a href="/collections/{g["k"]}/">{g["t"]}</a></li>' for g in GROUPS)
    return f"""<footer class="foot dark">
  <div class="wrap">
    <div class="foot-grid five">
      <div class="foot-brand">
        <a href="/" aria-label="LusterLux home">
          <img class="foot-lockup" src="/assets/brand/lusterlux-lockup.webp?v={V}" alt="LusterLux" />
        </a>
        <p>Built by two detailers who spent four years maintaining a rental fleet,
           washing two to ten vehicles a day. Made in the USA.</p>
        <p class="demo-note"><b>Demo build.</b> A concept site produced by ProofPilot for
           LusterLux Auto Care. Product names, descriptions, prices and photography belong to
           LusterLux; checkout hands off to their live store.</p>
      </div>
      <div><h3>Shop</h3><ul>{shop}<li><a href="/collections/">All products</a></li></ul></div>
      <div><h3>What You Drive</h3><ul>{"".join(f'<li><a href="/collections/{w["k"]}/">{w["t"]}</a></li>' for w in WORLDS)}</ul></div>
      <div><h3>Learn</h3><ul>
        <li><a href="/pages/find-your-product/">Find Your Product</a></li>
        <li><a href="/pages/nanofusion/">NanoFusion</a></li>
        <li><a href="/blogs/guides/">Guides</a></li>
        <li><a href="/pages/community/">Community</a></li>
        <li><a href="/pages/about/">Our Story</a></li>
        <li><a href="/cart/">Cart</a></li>
      </ul></div>
      <div><h3>Company</h3><ul>
        <li><a href="mailto:support@lusterluxauto.com">support@lusterluxauto.com</a></li>
        <li><a href="tel:+14804169665">Brandon &middot; 480-416-9665</a></li>
        <li><a href="tel:+14808481453">Chase &middot; 480-848-1453</a></li>
        <li><a href="{STORE}/policies/shipping-policy">Shipping</a></li>
        <li><a href="{STORE}/policies/refund-policy">Returns</a></li>
        <li><a href="{STORE}/policies/privacy-policy">Privacy</a></li>
        <li><a href="{STORE}/policies/terms-of-service">Terms</a></li>
      </ul></div>
    </div>
    <div class="foot-bot">
      <p>&copy; 2026 LusterLux. Free shipping on orders over {money(FREE)}.</p>
      <p>Mon&ndash;Fri, 8am&ndash;5pm &middot; replies in 2&ndash;8h</p>
    </div>
  </div>
</footer>
{drawer()}
<script>window.LL_BASE={json.dumps(BASE)};</script>
<script src="/data/catalog.js?v={V}"></script>
<script src="/assets/cart.js?v={V}"></script>
<script src="/assets/site.js?v={V}"></script>
</body>
</html>"""

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + '</script>'

def meta_desc(*parts, floor=125, cap=158):
    """Compose a description from real facts and land it in the 125-158 range."""
    out = ""
    for p in parts:
        p = plain(p).strip()
        if not p:
            continue
        cand = (out + " " + p).strip() if out else p
        if len(cand) > cap:
            if len(out) >= floor:
                break
            cand = cand[:cap].rsplit(" ", 1)[0].rstrip(" ,.;—-")
            out = cand
            break
        out = cand
        if len(out) >= floor:
            break
    return out


def crumbs(trail):
    out = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": []}
    for i, (name, url) in enumerate(trail, 1):
        out["itemListElement"].append({"@type": "ListItem", "position": i, "name": name,
                                       "item": SITE + url})
    return out

def crumb_nav(trail):
    parts = []
    for i, (name, url) in enumerate(trail):
        parts.append(f'<a href="{url}">{name}</a>' if i < len(trail) - 1 else f'<span aria-current="page">{name}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<i>/</i>'.join(parts) + '</nav>'

# ------------------------------------------------------------ product card --
def card(p, small=True):
    img = f'/assets/products/{p["img"]}{"-sm" if small else ""}.webp?v={V}'
    price = ('<span class="card-price soon">Coming soon</span>' if p["soon"]
             else f'<span class="card-price">{money(p["price"])}</span>')
    btn = ('' if p["soon"] else
           f'<button class="add" type="button" data-add="{p["h"]}" aria-label="Add {plain(p["n"])} to cart">'
           '<svg viewBox="0 0 24 24" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></button>')
    return f"""<article class="card" style="--acc:{p['acc']}">
  <a class="card-fig" href="{p['url']}" tabindex="-1" aria-hidden="true">
    <img src="{img}" alt="LusterLux {plain(p['n'])} {plain(p['fn'])}" loading="lazy" decoding="async" /></a>
  <div class="card-body">
    <p class="card-cat">{prod_sub_name(p)}</p>
    <h3><a href="{p['url']}">{esc(p['n'])}<span>{p['fn']}</span></a></h3>
    <p class="card-blurb">{p['short']}</p>
    <div class="card-foot">{price}{btn}</div>
  </div>
</article>"""

def md(src):
    """Minimal markdown: ### headings, **bold**, [links](/x/), - lists, 1. lists."""
    out, buf, mode = [], [], None
    def flush():
        nonlocal buf, mode
        if not buf: return
        if mode == "ul":   out.append("<ul class=\"md-ul\">" + "".join(f"<li>{x}</li>" for x in buf) + "</ul>")
        elif mode == "ol": out.append("<ol class=\"md-ol\">" + "".join(f"<li>{x}</li>" for x in buf) + "</ol>")
        buf, mode = [], None
    def inline(x):
        x = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', x)
        x = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", x)
        return x
    for raw in src.strip().split("\n"):
        line = raw.strip()
        if not line:
            flush(); continue
        if line.startswith("### "):
            flush(); out.append(f"<h2>{inline(line[4:])}</h2>"); continue
        if line.startswith("- "):
            if mode != "ul": flush(); mode = "ul"
            buf.append(inline(line[2:])); continue
        m = re.match(r"^(\d+)\. (.+)", line)
        if m:
            if mode != "ol": flush(); mode = "ol"
            buf.append(inline(m.group(2))); continue
        flush(); out.append(f"<p>{inline(line)}</p>")
    flush()
    return "\n".join(out)


_ABS = re.compile(r'(href|src)="/(?!/)')
_JS  = re.compile(r"""(['"])/(assets|collections|products|pages|blogs|cart|data)/""")

def rebase(html_str):
    """Prefix every root-relative path with BASE so the site works from a subpath."""
    if not BASE:
        return html_str
    out = _ABS.sub(lambda m: f'{m.group(1)}="{BASE}/', html_str)
    out = _JS.sub(lambda m: f"{m.group(1)}{BASE}/{m.group(2)}/", out)
    return out


def write(path, content):
    full = os.path.join(ROOT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if full.endswith((".html", ".xml", ".txt", ".csv")):
        content = rebase(content) if full.endswith(".html") else content
    open(full, "w").write(content)
    return full


def before_after():
    return f"""<div class="ba fade" data-d="2" id="ba">
  <div class="ba-stage" id="baStage">
    <img class="ba-img ba-after" src="/assets/scene/ba-after.webp?v={V}" alt="A McLaren 720S rinsed clean after a LuxFoam wash" loading="lazy" decoding="async" />
    <div class="ba-clip" id="baClip">
      <img class="ba-img" src="/assets/scene/ba-before.webp?v={V}" alt="The same McLaren 720S blanketed in LuxFoam before rinsing" loading="lazy" decoding="async" />
    </div>
    <span class="ba-label ba-l">Foamed</span>
    <span class="ba-label ba-r">Rinsed</span>
    <input class="ba-range" id="baRange" type="range" min="0" max="100" value="50"
           aria-label="Reveal the washed side" />
    <span class="ba-handle" id="baHandle" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6 4 12l5 6M15 6l5 6-5 6"/></svg></span>
  </div>
  <p class="ba-cap">One wash with <a href="/products/luxfoam-foam-cannon-soap/">LuxFoam</a>. Drag to compare.</p>
</div>"""


# ================================================================ HOMEPAGE ==
def showcase(p, i, total):
    """One product, full width. Big bottle, what it is, what it does, buy it."""
    specs = "".join(f"<li>{s}</li>" for s in p["specs"])
    feat4 = "".join(f'<li><b>{lead}</b> {body}</li>' for lead, body in (p.get("features") or [])[:4])
    return f"""<section class="show{' alt' if i % 2 else ''}" id="p-{p['img']}" style="--acc:{p['acc']}">
  <div class="wrap show-in">
    <div class="show-media {'dive-l' if i % 2 else 'dive-r'}">
      <div class="stage has-scene">
        {f'<img class="stage-scene" src="/assets/scene/{p["inuse"]}.webp?v={V}" alt="{esc(plain(p["n"]))} in use" loading="lazy" decoding="async" />' if p.get('inuse') else ''}
        <span class="stage-badge">{p['fn']}</span>
        {f'<span class="stage-size">{p["size"]}</span>' if p['size'] else ''}
        <div class="plinth">
          <img class="bottle" src="/assets/products/{p['img']}.webp?v={V}" alt="{esc(plain(p['title']))} by LusterLux" loading="lazy" decoding="async" />
          <img class="refl" src="/assets/products/{p['img']}.webp?v={V}" alt="" aria-hidden="true" loading="lazy" decoding="async" />
        </div>
      </div>
    </div>
    <div class="show-info fade">
      <p class="show-idx"><b>{i+1:02d}</b> &frasl; {total:02d} &middot; <a href="/collections/{prod_sub(p)}/">{prod_sub_name(p)}</a></p>
      <p class="show-sub">{p['fn']}</p>
      <h3 class="show-name">{esc(p['n'])}</h3>
      {f'<p class="show-line">{p["line"]}</p>' if p['line'] else ''}
      <p class="show-copy">{p.get('showBody') or p['short']}</p>
      {f'<ul class="feat show-feat">{feat4}</ul>' if feat4 else f'<ul class="show-specs">{specs}</ul>'}
      <div class="show-buy">
        <span class="show-price">{money(p['price'])}<small>{p['size']}</small></span>
        <button class="btn btn-primary add" type="button" data-add="{p['h']}">Add to cart
          <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button>
        <a class="tlink" href="{p['url']}">Full details<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      </div>
    </div>
  </div>
</section>"""


def build_home():
    heroes = sorted([p for p in P if p["hero"]], key=lambda p: p["hero"])
    line_cards = "".join(showcase(p, i, len(heroes)) for i, p in enumerate(heroes))

    system = [
      ("01", "Foam", "luxfoam-foam-cannon-soap", "Blanket it and let the soap lift the grit before anything touches paint."),
      ("02", "Wash", "luxpro-waterless-wash-detail-spray", "Contact wash, or skip the hose entirely with a waterless pass."),
      ("03", "Wheels &amp; Tires", "luxwheelassassin-wheel-cleaner", "Brake dust off the barrels, then dress the sidewalls last."),
      ("04", "Interior", "interiorx-interior-cleaner", "Dash, console and door cards back to a factory matte."),
      ("05", "Protect", "ceramicx-ceramic-detail-spray", "Lay down the ceramic layer that makes the next wash easier."),
    ]
    steps = "".join(
      f"""<li class="sys-step fade" data-d="{i}" style="--acc:{by_handle[h]['acc']}">
        <span class="sys-n">{n}</span>
        <a class="sys-fig" href="{by_handle[h]['url']}">
          <img src="/assets/products/{by_handle[h]['img']}-sm.webp?v={V}" alt="{esc(plain(by_handle[h]['title']))}" loading="lazy" decoding="async" /></a>
        <h3>{label}</h3><p>{copy}</p>
        <a class="tlink" href="{by_handle[h]['url']}">{by_handle[h]['n']}<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      </li>""" for i, (n, label, h, copy) in enumerate(system))

    beyond = "".join(
      f"""<a class="vcard fade" data-d="{i}" href="/collections/beyond-the-car/">
        <img src="/assets/scene/{img}.webp?v={V}" alt="{alt}" style="object-position:{pos}" loading="lazy" decoding="async" />
        <span class="vtag">{tag}</span>
        <div class="vcard-body"><h3>{title}</h3><p>{copy}</p>
        <span class="tlink">{cta}<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></span></div></a>"""
      for i, (img, alt, pos, tag, title, copy, cta) in enumerate([
        ("cart-sm", "BirdieLux golf cart cleaner beside a golf cart and bag", "50% 48%", "Golf Cart", "Carts",
         "BirdieLux and XFresh are built for cart paint, plastic panels and seats. Waterless, so no hose on the course.", "Shop cart care"),
        ("marine-sm", "LusterLux brushes and cleaners beside a boat", "50% 74%", "Marine", "Boats",
         "Gelcoat, vinyl seating and trim take sun and salt harder than anything on the road.", "Shop marine care"),
        ("hero-hood-sm", "Thick foam clinging to the body of a vehicle mid-wash", "50% 40%", "Off-Road", "Trucks &amp; UTVs",
         "Mud, dust and trail film. The same wheel cleaner and trim restorer, aimed at a harder job.", "Shop off-road"),
      ]))

    reviews = [
      ("Dr. Handshoes", "luxpro-waterless-wash-detail-spray",
       "I&rsquo;ve tried them all and have a whole shelf full of different companies and products &mdash; until now. I&rsquo;ve cleared out the shelf and filled it with LusterLux. This stuff works, like actually works."),
      ("Lucas Greenbank", "luxtowel-drying-towel", "Chase and Brandon are fantastic to work with. Their professionalism, knowledge, and passion for car care really stand out. From their drying towels to tire venom and protectants, they have delivered great results."),
      ("Tammy C", "ceramicx-ceramic-detail-spray", "I have been using LusterLux on my black vehicle for months now. It really protects it from water spotting. My car is always shiny and looks like it just rolled off the lot."),
      ("Hank H", "restorx-rvp-plastic-dressing", "Was skeptical to purchase the RestorX for the interior of my truck but am glad I did. The results exceeded my expectations and the shine has maintained longer than the Armor All I had always used prior."),
      ("Bree", "interiorx-interior-cleaner", "As a busy mom of three, my car is basically a second home &mdash; filled with crumbs, fingerprints, and the chaos of everyday life. I honestly didn&rsquo;t expect much, but LusterLux completely exceeded my expectations."),
    ]
    stars = ('<span class="stars" aria-label="5 out of 5">' +
             '<svg viewBox="0 0 24 24"><path d="m12 2 3 6.6 7 .8-5.2 4.8 1.4 7L12 17.8 5.8 21.2l1.4-7L2 9.4l7-.8L12 2Z"/></svg>' * 5 +
             '</span>')
    rcards = "".join(
      f'<article class="rcard">'
      f'<a class="rcard-fig" href="{by_handle[h]["url"]}" tabindex="-1" aria-hidden="true">'
      f'<img src="/assets/products/{by_handle[h]["img"]}-sm.webp?v={V}" '
      f'alt="LusterLux {plain(by_handle[h]["n"])}" loading="lazy" decoding="async" /></a>'
      f'<div class="rcard-body">{stars}<blockquote>{q}</blockquote>'
      f'<footer><cite>{who}</cite>'
      f'<a class="rcard-prod" href="{by_handle[h]["url"]}">{by_handle[h]["n"]}</a></footer></div>'
      f'</article>'
      for who, h, q in reviews)

    schema = [
      {"@context":"https://schema.org","@type":"Organization","@id":SITE+"/#org","name":"LusterLux",
       "alternateName":"Luster Lux Auto Care","url":SITE+"/","email":"support@lusterluxauto.com",
       "logo":SITE+"/assets/brand/favicon-512.png",
       "description":"Car care built by detailers, engineered with NanoFusion Surface Technology. Made in the USA.",
       "founder":[{"@type":"Person","name":"Brandon"},{"@type":"Person","name":"Chase"}],
       "contactPoint":[{"@type":"ContactPoint","contactType":"customer support",
         "email":"support@lusterluxauto.com","telephone":"+1-480-416-9665","availableLanguage":"English",
         "hoursAvailable":{"@type":"OpeningHoursSpecification",
           "dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday"],"opens":"08:00","closes":"17:00"}}],
       "aggregateRating":{"@type":"AggregateRating","ratingValue":"5.00","reviewCount":"17","bestRating":"5"}},
      {"@context":"https://schema.org","@type":"WebSite","url":SITE+"/","name":"LusterLux",
       "publisher":{"@id":SITE+"/#org"},
       "potentialAction":{"@type":"SearchAction",
         "target":{"@type":"EntryPoint","urlTemplate":SITE+"/collections/?q={search_term_string}"},
         "query-input":"required name=search_term_string"}},
      {"@context":"https://schema.org","@type":"ItemList","name":"The LusterLux line",
       "itemListElement":[{"@type":"ListItem","position":i+1,"item":{
         "@type":"Product","name":p["title"],"description":p["short"],
         "brand":{"@type":"Brand","name":"LusterLux"},"url":SITE+p["url"],
         "image":SITE+f'/assets/products/{p["img"]}.webp',
         "offers":{"@type":"Offer","price":f'{p["price"]:.2f}',"priceCurrency":"USD",
                   "availability":"https://schema.org/InStock","url":SITE+p["url"]}}}
         for i,p in enumerate(heroes)]},
    ]

    body = f"""{nav()}
<main id="main">

<section class="hero" id="hero">
  <div class="hero-bg" id="heroBg" data-par="26">
    <figure class="on"><img src="/assets/scene/nano-hood.webp?v={V}" alt="LuxPro waterless wash on the hood of a pearl-white sports car" style="object-position:50% 46%" fetchpriority="high" decoding="async" /></figure>
    <figure><img src="/assets/scene/hero-wheel.webp?v={V}" alt="A performance wheel with red brake calipers beside a bottle of LusterLux wheel cleaner" style="object-position:50% 48%" loading="lazy" decoding="async" /></figure>
    <figure><img src="/assets/scene/hero-foam.webp?v={V}" alt="A sports car covered in thick LuxFoam during a foam-cannon wash" style="object-position:50% 62%" loading="lazy" decoding="async" /></figure>
  </div>
  <div class="hero-veil"></div>
  <div class="hero-glow"></div>
  <div class="hero-in">
    <p class="kick rev">NanoFusion Surface Technology</p>
    <h1 class="rev d1">More than just a <em>clean car.</em></h1>
    <p class="lead rev d2">Four years on a rental fleet taught us what actually works and what just looks good in the bottle. So we built the line ourselves.</p>
    <div class="hero-ctas rev d3">
      <a class="btn btn-primary" href="/collections/">Shop the Line<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      <a class="btn btn-ghost" href="/pages/find-your-product/">Find your product</a>
    </div>
    <ul class="hero-strip rev d4">
      <li>Made in the USA</li>
      <li>Safe on PPF, wraps &amp; ceramic</li>
      <li>Free shipping over {money(FREE)}</li>
    </ul>
    <div class="hero-dots" id="heroDots">
      <button type="button" aria-label="Show slide 1" aria-current="true"></button>
      <button type="button" aria-label="Show slide 2" aria-current="false"></button>
      <button type="button" aria-label="Show slide 3" aria-current="false"></button>
    </div>
  </div>
</section>

<div class="strip" aria-hidden="true"><div class="strip-in">{strip_items()}{strip_items()}</div></div>

<section class="sec bone" id="categories">
  <div class="wrap">
    <div class="sec-head">
      <p class="kick slide">Shop by Category</p>
      <h2 class="fade" data-d="1">Know what you need? <em>Start here.</em></h2>
      <p class="lead fade" data-d="2">Five aisles, twelve shelves, every product on one of them. Not sure which?
        <a class="lime" href="/pages/find-your-product/">Answer two questions</a> and we will name the bottle.</p>
    </div>
    <div class="ctiles fade" data-d="2">{cat_tiles()}</div>
  </div>
</section>

<div class="shows" id="line">
  <div class="wrap">
    <div class="sec-head" style="padding-top:clamp(74px,9vw,130px)">
      <p class="kick slide">The Line</p>
      <h2 class="fade" data-d="1">Six bottles. <em>Every surface.</em></h2>
      <p class="lead fade" data-d="2">Each one does a single job properly. No shelf of half-used bottles you never reach for again.</p>
    </div>
  </div>
  {line_cards}
  <div class="wrap" style="padding-bottom:clamp(74px,9vw,130px)">
    <a class="tlink" href="/collections/">See all {len(P)} products<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
  </div>
</div>

<section class="sec bone" id="nanofusion">
  <div class="wrap">
    <div class="nano-top">
      <div class="sec-head">
        <p class="kick slide">The Technology</p>
        <h2 class="fade" data-d="1">The dirt leaves. <em>It doesn&rsquo;t travel.</em></h2>
        <p class="lead fade" data-d="2">A swirl is a piece of grit held against your clear coat by a towel and dragged twelve inches. NanoFusion wraps that grit in nano-polymer and floats it clear of the paint, then leaves a slick hydrophobic layer behind when it goes.</p>
        <p class="fade" data-d="3" style="margin-top:26px"><a class="tlink" href="/pages/nanofusion/">How it works<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></p>
      </div>
      <figure class="nano-fig fade" data-d="2">
        <img src="/assets/scene/nano-hood.webp?v={V}" alt="LuxPro waterless wash being applied to the hood of a pearl-white sports car" loading="lazy" decoding="async" />
        <figcaption>LuxPro on a pearl finish &mdash; spray, wipe, done</figcaption>
      </figure>
    </div>
    <ol class="flow">{nano_steps()}</ol>
  </div>
</section>

<section class="sec" id="story">
  <div class="wrap story-grid">
    <div class="story-copy">
      <p class="kick slide">Why We Started</p>
      <h2 class="fade" data-d="1">Chase <em>&amp;</em> Brandon.</h2>
      <p class="fade" data-d="2">We didn&rsquo;t start this because the world needed another detailing brand.
        We started it because the products we depended on every day weren&rsquo;t doing what they promised.</p>
      <p class="fade" data-d="2">Running a rental car business meant cleaning and detailing vehicle after
        vehicle. Streaky finishes. Greasy interior dressings. Tire shine that lasted a weekend. So we spent
        a long time testing and reformulating until we had products that solved the problems we were
        actually having &mdash; and we still test every formula against real vehicles in Arizona sun before
        it goes in a bottle.</p>
      <p class="fade" data-d="3">We&rsquo;re Chase and Brandon. When we&rsquo;re not detailing you&rsquo;ll find us
        at the Glamis dunes, riding up north in Heber, or out on the dirt trails &mdash; which is exactly why
        this line has to hold up on more than a garage queen.</p>
      <p class="sign fade" data-d="3"><b>Chase &amp; Brandon</b> &middot; Founders, Arizona</p>
      <p class="fade" data-d="3" style="margin-top:26px">
        <a class="btn btn-primary" href="/pages/about/">Read the full story
          <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></p>
    </div>
    <figure class="story-fig fade" data-d="2">
      <img src="/assets/scene/founders.webp?v={V}" alt="Chase and Brandon, the founders of LusterLux, with their trucks in the Arizona desert" loading="lazy" decoding="async" />
    </figure>
  </div>
</section>

<section class="sec bone" id="the-work">
  <div class="wrap">
    <div class="sec-head c">
      <p class="kick c slide">Foam. Rinse. Shine.</p>
      <h2 class="fade" data-d="1">One wash. <em>Drag it.</em></h2>
      <p class="lead fade" data-d="2">A 720S blanketed in LuxFoam and rinsed. Same car, same camera, four minutes apart.</p>
    </div>
    {before_after()}
  </div>
</section>

<section class="sec" id="guides">
  <div class="wrap">
    <div class="sec-head">
      <p class="kick slide">Guides</p>
      <h2 class="fade" data-d="1">Do it properly, <em>the first time.</em></h2>
      <p class="lead fade" data-d="2">Written by the people who washed the fleet. The steps, the order, and the mistakes that cost you paint.</p>
    </div>
    <div class="grid three fade" data-d="2">{"".join(guide_card(g) for g in GUIDES[:3])}</div>
    <p class="fade" data-d="3" style="margin-top:32px"><a class="tlink" href="/blogs/guides/">All {len(GUIDES)} guides<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></p>
  </div>
</section>

<section class="sec bone revs" id="reviews">
  <div class="wrap">
    <div class="rev-head">
      <div>
        <p class="kick slide">Reviews</p>
        <h2 class="fade" data-d="1">The hardest crowd <em>there is.</em></h2>
      </div>
      <p class="rev-score fade" data-d="1"><b>5.00</b>
        <span class="stars" aria-label="5 out of 5">{stars_svg()}</span>
        <em>17 verified reviews</em></p>
    </div>
    <div class="rev-rail" id="revRail">{rcards}</div>
    <div class="rev-ctrl">
      <button id="revPrev" type="button" aria-label="Previous reviews"><svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg></button>
      <button id="revNext" type="button" aria-label="More reviews"><svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg></button>
    </div>
  </div>
</section>

<section class="sec bone" id="community">
  <div class="wrap">
    <div class="ig-head">
      <a class="ig-av" href="{IG}" target="_blank" rel="noopener"
         aria-label="LusterLux on Instagram">
        <img src="/assets/brand/lusterlux-mark-320.webp?v={V}" alt="" width="218" height="320" /></a>
      <div class="ig-id">
        <p class="ig-handle"><a href="{IG}" target="_blank" rel="noopener">@lusterluxauto</a></p>
        <p class="ig-name">LusterLux Auto Care</p>
        <p class="ig-bio">Detailing products engineered with NanoFusion. Made in the USA.
          Daily drivers, project cars, carts, boats and work trucks.</p>
      </div>
      <div class="ig-cta">
        <a class="btn btn-primary" href="{IG}" target="_blank" rel="noopener">Follow on Instagram
          <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
        <p class="ig-more"><a href="{TT}" target="_blank" rel="noopener">TikTok</a>
          <a href="{YT}" target="_blank" rel="noopener">YouTube</a>
          <a href="{FB}" target="_blank" rel="noopener">Facebook</a></p>
      </div>
    </div>
    <div class="ig-grid">{ig_grid()}</div>
    <p class="ig-note">Photography by LusterLux. Tiles open their Instagram profile.</p>
  </div>
</section>

</main>
{footer()}"""
    extra = f'<link rel="preload" as="image" href="/assets/scene/nano-hood.webp?v={V}" />\n' + "\n".join(ld(s) for s in schema) + "\n"
    write("/index.html", head("Car Detailing Products Engineered with NanoFusion | LusterLux",
        meta_desc("Car care built by detailers — waterless wash, ceramic spray, foam soap, wheel and tire care, and interior.",
                  "Engineered with NanoFusion Surface Technology. Made in the USA."),
        "/", extra) + body)


# =========================================================== FIND YOUR PRODUCT
SURFACES = [
  ("car-truck",   "Car or truck",  "M3.4 14.7h17.2M5.7 14.7 7.5 9.4a2.2 2.2 0 0 1 2.1-1.5h4.8a2.2 2.2 0 0 1 2.1 1.5l1.8 5.3"),
  ("golf-cart",   "Golf cart",     "M3 15h13l2-5h3M6 15v3M16 15v3M4 10h8v5"),
  ("boat-marine", "Boat or marine","M4 17h16l-2.2 4H6.2ZM12 3v11M12 5l6 9H6Z"),
  ("off-road",    "Off-road / UTV","M3.4 14.7h17.2M6 14.7 8 9.2h8l2 5.5M6.4 17.4a2.6 2.6 0 1 0 5.2 0 2.6 2.6 0 1 0-5.2 0M13.4 17.4a2.6 2.6 0 1 0 5.2 0 2.6 2.6 0 1 0-5.2 0"),
]
JOBS = [
  ("full-wash",    "Full wash"),
  ("quick-clean",  "Quick clean, no water"),
  ("wheels-tires", "Wheels and tires"),
  ("interior",     "Interior"),
  ("restore-trim", "Restore faded trim"),
]
# (surface, job) -> primary handle, pairing handle, kit handle, reason
RESULTS = {
 ("car-truck","full-wash"):    ("luxfoam-foam-cannon-soap","luxmit-wash-mit","foam-wash-system-1",
   "A contact wash is where swirls come from. Thick foam does the lifting first, so the mitt is gliding on lubricant instead of grinding grit."),
 ("car-truck","quick-clean"):  ("luxpro-waterless-wash-detail-spray","3-pack-edgeless-lux-edgeless-microfiber-towels","waterless-wash-system-1",
   "Light dust, pollen and fingerprints do not need a hose. NanoFusion encapsulates them so they lift off instead of dragging across the clear coat."),
 ("car-truck","wheels-tires"): ("luxwheelassassin-wheel-cleaner","tirevenom-tire-dressing","rim-and-tire-system-kit-1",
   "Break the brake dust down chemically, then dress the sidewall last so nothing gets slung onto clean paint."),
 ("car-truck","interior"):     ("interiorx-interior-cleaner","5-pack-microlux-microfiber-towels","complete-interior-system-1",
   "Cleans to a factory matte, so nothing reflects in the windshield and the wheel does not end up slick."),
 ("car-truck","restore-trim"): ("restorx-rvp-plastic-dressing","2-pack-xpad-applicator-pad","interior-restoration-system-1",
   "Faded grey trim is what makes a clean car still look old. RestorX levels into the surface rather than sitting on it."),

 ("golf-cart","full-wash"):    ("birdielux-golf-cart-exterior-cleaner","3-pack-edgeless-lux-edgeless-microfiber-towels","fairway-finish-system",
   "Carts rarely live near a hose. BirdieLux cleans painted panels and plastic bodywork where the cart sits."),
 ("golf-cart","quick-clean"):  ("birdielux-golf-cart-exterior-cleaner","3-pack-edgeless-lux-edgeless-microfiber-towels","fairway-finish-system",
   "Cart-path dust wipes off waterless without streaking the panels."),
 ("golf-cart","wheels-tires"): ("luxwheelassassin-wheel-cleaner","tirevenom-tire-dressing","tire-care-system-1",
   "Cart wheels take the same brake dust and path grime, on a smaller scale. Same two bottles, less of each."),
 ("golf-cart","interior"):     ("xfresh-golf-cart-interior-cleaner","5-pack-microlux-microfiber-towels","fairway-finish-system",
   "Cart seats live outdoors and take sunscreen and sweat all season. XFresh dries clean, which matters on a bench seat with no belts."),
 ("golf-cart","restore-trim"): ("restorx-rvp-plastic-dressing","2-pack-xpad-applicator-pad","fairway-finish-system",
   "Cart bodies are almost entirely plastic, and plastic is exactly what RestorX is built to bring back."),

 ("boat-marine","full-wash"):  ("luxfoam-foam-cannon-soap","luxmit-wash-mit","foam-wash-system-1",
   "Salt needs volume and dwell time to come off gelcoat safely. Foam gives you both."),
 ("boat-marine","quick-clean"):("luxpro-waterless-wash-detail-spray","3-pack-edgeless-lux-edgeless-microfiber-towels","waterless-wash-system-1",
   "For a wipe-down at the slip where there is no wash bay, and spray-off is not an option."),
 ("boat-marine","wheels-tires"):("luxwheelassassin-wheel-cleaner","tirevenom-tire-dressing","rim-and-tire-system-kit-1",
   "Trailer wheels take road grime and brake dust the whole way to the ramp, then sit in salt water."),
 ("boat-marine","interior"):   ("xfresh-golf-cart-interior-cleaner","5-pack-microlux-microfiber-towels","complete-interior-system-1",
   "Marine vinyl seating is the same problem as a cart bench: it has to come clean without turning slick."),
 ("boat-marine","restore-trim"):("restorx-rvp-plastic-dressing","2-pack-xpad-applicator-pad","interior-restoration-system-1",
   "Sun and salt fade rubber and plastic faster than anything on the road. RestorX holds up to eight months."),

 ("off-road","full-wash"):     ("luxfoam-foam-cannon-soap","luxcannon-foam-cannon","foam-wash-system-1",
   "Dried mud has to be softened, not scrubbed. Blanket it, let it dwell, then rinse before anything touches the panel."),
 ("off-road","quick-clean"):   ("luxpro-waterless-wash-detail-spray","3-pack-edgeless-lux-edgeless-microfiber-towels","waterless-wash-system-1",
   "For trail dust only. If there is grit on the panel it needs a rinse first, waterless or not."),
 ("off-road","wheels-tires"):  ("luxwheelassassin-wheel-cleaner","tirevenom-tire-dressing","rim-and-tire-system-kit-1",
   "Beadlocks and heavy lugs hold onto everything. Chemical breakdown beats trying to brush it all out."),
 ("off-road","interior"):      ("interiorx-interior-cleaner","lux-brush-interior-brush","complete-interior-system-1",
   "Dust gets into every seam. The cleaner handles the panels, the brush handles the vents and switchgear."),
 ("off-road","restore-trim"):  ("restorx-rvp-plastic-dressing","2-pack-xpad-applicator-pad","interior-restoration-system-1",
   "Fender flares, bumpers and rocker cladding are the first things to chalk out. This is what brings them back."),
}

def finder_widget():
    s_btns = "".join(
      f'<button type="button" class="fq-opt" data-s="{k}"><svg viewBox="0 0 24 24" fill="none" '
      f'stroke-linecap="round" stroke-linejoin="round"><path d="{d}"/></svg><span>{label}</span></button>'
      for k, label, d in SURFACES)
    j_btns = "".join(f'<button type="button" class="fq-opt" data-j="{k}"><span>{label}</span></button>'
                     for k, label in JOBS)
    return f"""<div class="finder fade" data-d="2" id="finder">
  <div class="fq" data-step="1">
    <p class="fq-q"><b>1</b> What are you cleaning?</p>
    <div class="fq-opts">{s_btns}</div>
  </div>
  <div class="fq" data-step="2" hidden>
    <p class="fq-q"><b>2</b> What do you need to do?</p>
    <div class="fq-opts">{j_btns}</div>
    <button type="button" class="fq-back" data-back>&larr; Back</button>
  </div>
  <div class="fq-out" id="fqOut" hidden aria-live="polite"></div>
  <noscript><p class="fq-ns">Pick a combination from the <a href="/pages/find-your-product/">full product finder</a>.</p></noscript>
</div>"""

def result_block(sk, jk, heading_level="h2"):
    prim_h, pair_h, kit_h, why = RESULTS[(sk, jk)]
    prim, pair, kit = by_handle[prim_h], by_handle[pair_h], by_handle[kit_h]
    def mini(p, role):
        price = "Coming soon" if p["soon"] else money(p["price"])
        add = "" if p["soon"] else f'<button class="btn btn-primary btn-sm add" type="button" data-add="{p["h"]}">Add to cart</button>'
        return f"""<article class="res" style="--acc:{p['acc']}">
          <p class="res-role">{role}</p>
          <a class="res-fig" href="{p['url']}"><img src="/assets/products/{p['img']}-sm.webp?v={V}" alt="{esc(plain(p['title']))}" loading="lazy" decoding="async" /></a>
          <h3><a href="{p['url']}">{esc(p['n'])}</a><span>{p['fn']}</span></h3>
          <p class="res-price">{price}</p>{add}</article>"""
    return f"""<div class="res-out">
      <p class="res-why">{why}</p>
      <div class="res-grid">{mini(prim,"Start here")}{mini(pair,"Pair it with")}{mini(kit,"Or take the kit")}</div>
    </div>"""

def build_finder():
    rows = "".join(
      f'<li><a href="/pages/find-your-product/{sk}-{jk}/">'
      f'<b>{slabel}</b><span>{jlabel}</span>'
      f'<i>{by_handle[RESULTS[(sk,jk)][0]]["n"]}</i></a></li>'
      for sk, slabel, _ in SURFACES for jk, jlabel in JOBS)
    body = f"""{nav('find')}
<main id="main">
  <section class="page-head">
    <div class="wrap">
      {crumb_nav([("Home","/"),("Find Your Product","/pages/find-your-product/")])}
      <h1>Find your product.</h1>
      <p class="lead">Two questions, one answer. Tell us what you are cleaning and what you need to do, and we will name the bottle, what to pair it with, and the kit that covers it.</p>
    </div>
  </section>
  <section class="sec"><div class="wrap">{finder_widget()}</div></section>
  <section class="sec alt"><div class="wrap">
    <div class="sec-head"><p class="kick slide">Every combination</p>
      <h2 class="fade" data-d="1">All {len(RESULTS)} answers.</h2>
      <p class="lead fade" data-d="2">Each one has its own page, so you can link straight to the answer.</p></div>
    <ul class="res-index fade" data-d="2">{rows}</ul>
  </div></section>
</main>
{footer()}"""
    write("/pages/find-your-product/index.html",
      head("Find Your Product | LusterLux",
           "Two questions and we will name the product. Pick what you are cleaning — car, golf cart, boat or off-road — and the job, and get the bottle, the pairing and the kit.",
           "/pages/find-your-product/",
           ld(crumbs([("Home","/"),("Find Your Product","/pages/find-your-product/")]))) + body)

    for sk, slabel, _ in SURFACES:
        for jk, jlabel in JOBS:
            url = f"/pages/find-your-product/{sk}-{jk}/"
            prim = by_handle[RESULTS[(sk, jk)][0]]
            title = f"{jlabel} for a {slabel.lower()} | LusterLux"
            desc = meta_desc(f"{slabel}, {jlabel.lower()}: start with {prim['n']} — {prim['fn']}.",
                             RESULTS[(sk, jk)][3],
                             f"Free shipping over {money(FREE)}.")
            trail = [("Home","/"),("Find Your Product","/pages/find-your-product/"),(f"{slabel} · {jlabel}",url)]
            b = f"""{nav('find')}
<main id="main">
  <section class="page-head">
    <div class="wrap">
      {crumb_nav(trail)}
      <p class="kick">{slabel}</p>
      <h1>{jlabel} &mdash; <em>what to use.</em></h1>
    </div>
  </section>
  <section class="sec"><div class="wrap">{result_block(sk, jk)}</div></section>
  <section class="sec alt"><div class="wrap">
    <div class="sec-head"><h2>Different job?</h2></div>
    <ul class="res-index">{''.join(
      f'<li><a href="/pages/find-your-product/{sk}-{k2}/"><b>{slabel}</b><span>{l2}</span>'
      f'<i>{by_handle[RESULTS[(sk,k2)][0]]["n"]}</i></a></li>' for k2, l2 in JOBS if k2 != jk)}</ul>
    <p style="margin-top:28px"><a class="tlink" href="/pages/find-your-product/">Start the finder over<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></p>
  </div></section>
</main>
{footer()}"""
            write(url + "index.html", head(title, desc, url, ld(crumbs(trail))) + b)


def nano_steps():
    """One connected diagram. Three boxes in a row was the copy-paste tell."""
    steps = [
      ("01", "Encapsulate", "Wrapped, not smeared",
       "Nano-polymers surround each particle of dust, pollen and road film so it is suspended away from the finish before a towel ever touches it.",
       '<circle cx="24" cy="24" r="14"/><circle cx="24" cy="24" r="5.5"/><path d="M24 4v5M24 39v5M4 24h5M39 24h5M10 10l3.5 3.5M34.5 34.5 38 38M38 10l-3.5 3.5M13.5 34.5 10 38"/>'),
      ("02", "Glide", "Lubricity does the work",
       "A high-slip layer lets the towel travel instead of grabbing. This is the single biggest thing standing between a maintenance wipe and a panel full of swirls.",
       '<path d="M6 30c6-9 12-9 18 0s12 9 18 0"/><path d="M6 39h36"/><path d="M17 16c0-4 3-7 7-7s7 3 7 7"/><path d="M24 9V4"/>'),
      ("03", "Seal", "Protection stays behind",
       "What is left on the panel is an invisible, hydrophobic film \u2014 more gloss, tighter beading, less dust adhesion, and a car that stays clean longer between washes.",
       '<path d="M24 5 40 11v11.5C40 32 33.2 38.6 24 42c-9.2-3.4-16-10-16-19.5V11L24 5Z"/><path d="m17.5 23.5 4.5 4.5 9-9.5"/>'),
    ]
    return "".join(
      f'<li class="flow-step fade" data-d="{i}">'
      f'<span class="flow-num">{n}</span>'
      f'<span class="flow-node"><svg viewBox="0 0 48 48" fill="none" stroke-linecap="round" stroke-linejoin="round">{ic}</svg></span>'
      f'<span class="flow-tag">{tag}</span>'
      f'<h3>{title}</h3><p>{copy}</p></li>'
      for i, (n, tag, title, copy, ic) in enumerate(steps))


# ============================================================== COLLECTIONS ==
def collection_page(key, title, desc, items, url, intro="", world=False, subnav="", parent=""):
    cards = "".join(card(p) for p in items) or '<p class="empty">Nothing here yet.</p>'
    chips = "".join(
      f'<a class="chip{" on" if g["k"]==key else ""}" href="/collections/{g["k"]}/">{g["t"]}'
      f'<b>{len(in_group(g["k"]))}</b></a>' for g in GROUPS)
    wchips = "".join(
      f'<a class="chip w{" on" if w["k"]==key else ""}" href="/collections/{w["k"]}/">{w["t"]}'
      f'<b>{len(in_world(w["k"]))}</b></a>' for w in WORLDS)
    trail = [("Home","/"),("Shop","/collections/")]
    if parent: trail.append((plain(group_meta(parent)["t"]), f'/collections/{parent}/'))
    if key: trail.append((title, url))
    sch = [crumbs(trail),
      {"@context":"https://schema.org","@type":"CollectionPage","name":title,"url":SITE+url,
       "description":desc,
       "mainEntity":{"@type":"ItemList","numberOfItems":len(items),
        "itemListElement":[{"@type":"ListItem","position":i+1,"item":{
          "@type":"Product","name":p["title"],"description":p["short"],"url":SITE+p["url"],
          "image":SITE+f'/assets/products/{p["img"]}.webp',
          "brand":{"@type":"Brand","name":"LusterLux"},
          "offers":{"@type":"Offer","price":f'{p["price"]:.2f}',"priceCurrency":"USD",
                    "availability":"https://schema.org/InStock" if not p["soon"] else "https://schema.org/PreOrder",
                    "url":SITE+p["url"]}}} for i,p in enumerate(items)]}}]
    body = f"""{nav('shop')}
<main id="main">
  <section class="page-head">
    <div class="wrap">
      {crumb_nav(trail)}
      <h1>{title}</h1>
      <p class="lead">{intro or desc}</p>
      {f'<nav class="subnav">{subnav}</nav>' if subnav else ''}
    </div>
  </section>
  <div class="catbar"><div class="wrap catbar-in">
    <a class="chip{" on" if not key else ""}" href="/collections/">All<b>{len(P)}</b></a>{chips}
    <span class="chip-sep" aria-hidden="true"></span>{wchips}
    <div class="catbar-tools">
      <label class="srch"><span class="vh">Search products</span>
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4 4"/></svg>
        <input id="q" type="search" placeholder="Search" autocomplete="off" /></label>
      <label><span class="vh">Sort</span>
        <select class="sort" id="sort">
          <option value="featured">Featured</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
          <option value="name">Name: A&ndash;Z</option>
        </select></label>
    </div>
  </div></div>
  <div class="wrap">
    <p class="count" id="count" aria-live="polite">{len(items)} product{"" if len(items)==1 else "s"}</p>
    <div class="grid four" id="grid" data-cat="{key}">{cards}</div>
  </div>
</main>
{footer()}"""
    write(url + "index.html", head(title + " | LusterLux", desc, url,
          "\n".join(ld(s) for s in sch)) + body)


def build_collections():
    # five group pages, each listing its subcategories
    for g in GROUPS:
        items = in_group(g["k"])
        subnav = "".join(
          f'<a class="subchip" href="/collections/{sk}/">{sub_meta(sk)["t"]}'
          f'<b>{len(in_sub(sk))}</b></a>' for sk in g["subs"])
        collection_page(g["k"], plain(g["t"]),
          meta_desc(g["d"], f'{len(items)} LusterLux products in {plain(g["t"]).lower()}.',
                    f'Made in the USA. Free shipping over {money(FREE)}.'),
          items, f'/collections/{g["k"]}/', g["d"], subnav=subnav)
    # subcategory pages (the three Beyond-the-Car subs are the world pages, built below)
    for s in SUBS:
        if s["k"] in WORLD_KEYS: continue
        items = in_sub(s["k"])
        collection_page(s["k"], plain(s["t"]),
          meta_desc(s["d"], f'{len(items)} products in {plain(s["t"]).lower()} from LusterLux.',
                    f'Made in the USA. Free shipping over {money(FREE)}.'),
          items, f'/collections/{s["k"]}/', s["d"], parent=s["g"])

    collection_page("", "Shop all",
      meta_desc(f"Every LusterLux product in one place — all {len(P)} of them, across wash and waterless, wheels and tires, interior, towels and tools, kits, and beyond-the-car care.",
                f"Free shipping over {money(FREE)}."),
      P, "/collections/",
      "The whole catalog, grouped by what you are actually cleaning. Filter it, sort it, or search it.")
    for w in WORLDS:
        items = in_world(w["k"])
        collection_page(w["k"], w["t"].replace("&amp;", "&"),
          meta_desc(w["d"], f'{len(items)} LusterLux products that apply to {plain(w["t"]).lower()}.',
                    f'Made in the USA. Free shipping over {money(FREE)}.'),
          items, f'/collections/{w["k"]}/', w["d"], world=True,
          parent="beyond-the-car" if w["k"] in ("golf-cart","marine","off-road") else "")
    m = [p for p in P if p["cat"] == "merch"]
    collection_page("merch", "Merch",
      meta_desc("LusterLux tees and caps for the people who spend their weekends in the driveway rather than out of it.",
                f"Limited runs, and when a batch is gone it is gone. Free shipping over {money(FREE)}."),
      m, "/collections/merch/", "Wear it.")


# ================================================================= PRODUCTS ==
def build_products():
    for p in P:
        others = [by_handle[h] for h in p["pairs"] if h in by_handle]
        if len(others) < 2:
            same = [q for q in P if q["cat"] == p["cat"] and q["h"] != p["h"]
                    and q not in others and not q["soon"]]
            others += same[:2 - len(others)]
        pairs = "".join(card(q) for q in others[:2])
        best = "".join(f"<li>{b}</li>" for b in p["bestFor"])
        how  = "".join(f"<li>{s}</li>" for s in p["how"])
        specs = "".join(f"<li>{s}</li>" for s in p["specs"])
        gk = p.get("group") or "kits-systems"
        sk = prod_sub(p)
        trail = [("Home","/"),("Shop","/collections/"),
                 (plain(group_meta(gk)["t"]), f'/collections/{gk}/')]
        if sk != gk: trail.append((plain(prod_sub_name(p)), f'/collections/{sk}/'))
        trail.append((p["n"], p["url"]))
        inc = ("" if not p.get("includes") else
          '<h2 class="pdp-h">In the box</h2><ul class="includes">' +
          "".join(f'<li>{x}</li>' for x in p["includes"]) + '</ul>')
        who = ("" if not p.get("who") else
          f'<div class="whofor"><b>Who it is for</b><span>{p["who"]}</span></div>')
        feats = ("" if not p.get("features") else
          '<h2 class="pdp-h">What it does</h2><ul class="feat">' +
          "".join(f'<li><b>{lead}</b> {body}</li>' for lead, body in p["features"]) + '</ul>')
        caution = ("" if not p.get("caution") else
          f'<div class="caution"><b>{p["caution"][0]}</b><span>{p["caution"][1]}</span></div>')
        tips = ("" if not p.get("tips") else
          '<h2 class="pdp-h">Detailer tips</h2><ul class="tips">' +
          "".join(f'<li>{x}</li>' for x in p["tips"]) + '</ul>')

        buy = ('<p class="pdp-soon">Coming soon &mdash; not yet available to order.</p>' if p["soon"] else
               f"""<div class="pdp-buy">
                 <span class="pdp-price">{money(p['price'])}{f'<small>{p["size"]}</small>' if p['size'] else ''}</span>
                 <button class="btn btn-primary add" type="button" data-add="{p['h']}">Add to cart
                   <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button>
               </div>
               <p class="pdp-ship">Free shipping on orders over {money(FREE)} &middot; Made in the USA</p>""")

        faq = [
          ("Is it safe on my finish?", "Safe surfaces are listed above, straight from the product's own directions. If your finish is not on that list, test an inconspicuous area first."),
          ("How far does one bottle go?", p["coverage"] or "Coverage depends on vehicle size and how dirty it is. See the directions on the bottle."),
          ("Where is it made?", "Made in the USA, and formulated by two detailers who spent four years maintaining a rental fleet."),
          ("What does shipping cost?", f"Free on orders over {money(FREE)}. Support runs Monday to Friday, 8am to 5pm, with replies in two to eight hours."),
        ]
        faq_html = "".join(
          f'<details class="faq-item"><summary class="faq-q">{q}<span class="pm"></span></summary>'
          f'<div class="faq-a">{a}</div></details>' for q, a in faq)

        sch = [crumbs(trail),
          {"@context":"https://schema.org","@type":"Product","name":p["title"],
           "description":re.sub("<[^>]+>","",p["desc"]),
           "sku":p["h"],"brand":{"@type":"Brand","name":"LusterLux"},
           "image":[SITE+f'/assets/products/{p["img"]}.webp'],"url":SITE+p["url"],
           "aggregateRating":{"@type":"AggregateRating","ratingValue":"5.00","reviewCount":"17","bestRating":"5"},
           "offers":{"@type":"Offer","price":f'{p["price"]:.2f}',"priceCurrency":"USD",
             "availability":"https://schema.org/PreOrder" if p["soon"] else "https://schema.org/InStock",
             "url":SITE+p["url"],"seller":{"@type":"Organization","name":"LusterLux"}}},
          {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
            {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":re.sub("<[^>]+>","",a)}}
            for q,a in faq]}]
        if p["how"]:
            sch.append({"@context":"https://schema.org","@type":"HowTo",
              "name":f'How to use {p["n"]}',
              "step":[{"@type":"HowToStep","position":i+1,"text":re.sub("<[^>]+>","",s)}
                      for i,s in enumerate(p["how"])]})

        body = f"""{nav('shop')}
<main id="main">
  <div class="wrap">{crumb_nav(trail)}</div>
  <section class="pdp" style="--acc:{p['acc']}">
    <div class="wrap pdp-in">
      <div class="pdp-media">
        <div class="stage">
          <span class="stage-badge">{p['fn']}</span>
          {f'<span class="stage-size">{p["size"]}</span>' if p['size'] else ''}
          <div class="plinth">
            <img class="bottle" src="/assets/products/{p['img']}.webp?v={V}" alt="{esc(plain(p['title']))} by LusterLux" fetchpriority="high" decoding="async" />
            <img class="refl" src="/assets/products/{p['img']}.webp?v={V}" alt="" aria-hidden="true" decoding="async" />
          </div>
        </div>
      </div>
      <div class="pdp-info">
        <p class="pdp-cat"><a href="/collections/{sk}/">{prod_sub_name(p)}</a></p>
        <h1>{esc(p['n'])} <em>&mdash; {p['fn']}</em></h1>
        {f'<p class="pdp-line">{p["line"]}</p>' if p['line'] else ''}
        <p class="pdp-desc">{p['desc']}</p>
        {f'<ul class="pdp-specs">{specs}</ul>' if specs else ''}
        {buy}
        {f'<p class="pdp-note">{p["note"]}</p>' if p['note'] else ''}
      </div>
    </div>
  </section>

  <section class="sec alt">
    <div class="wrap pdp-detail">
      <div class="pdp-main">
        {inc}
        {feats}
        {who}
        {caution}
        {f'<h2 class="pdp-h">How to use</h2><ol class="steps-num">{how}</ol>' if how else ''}
        {tips}
      </div>
      <aside class="pdp-aside">
        {f'<h2 class="pdp-h">Best for</h2><ul class="tick">{best}</ul>' if best else ''}
        <h2 class="pdp-h">Good to know</h2>
        <div class="faq-list">{faq_html}</div>
      </aside>
    </div>
  </section>

  <section class="sec">
    <div class="wrap">
      <div class="sec-head"><p class="kick slide">Pairs with</p>
        <h2 class="fade" data-d="1">Works with {esc(p['n'])}.</h2></div>
      <div class="grid four fade" data-d="2">{pairs}</div>
      <p class="fade" data-d="3" style="margin-top:30px"><a class="tlink" href="/collections/{sk}/">All {prod_sub_name(p)}<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></p>
    </div>
  </section>
</main>
{footer()}"""
        meta = meta_desc(p["short"], p["coverage"],
                         f'{p["n"]} — {p["fn"]} from LusterLux.',
                         f'Made in the USA. Free shipping over {money(FREE)}.')
        write(p["url"] + "index.html",
              head(f'{p["title"]} | LusterLux', meta, p["url"],
                   "\n".join(ld(s) for s in sch)) + body)


# ==================================================================== PAGES ==
def build_cart():
    trail = [("Home","/"),("Cart","/cart/")]
    body = f"""{nav()}
<main id="main">
  <section class="page-head">
    <div class="wrap">{crumb_nav(trail)}<h1>Your cart.</h1></div>
  </section>
  <section class="sec"><div class="wrap cart-page">
    <div class="cart-page-main">
      <p class="free-bar" id="cartFree"></p>
      <ul class="cart-lines" id="cartLines"></ul>
    </div>
    <aside class="cart-page-side">
      <h2>Summary</h2>
      <p class="sub"><span>Subtotal</span><b id="cartSub">$0.00</b></p>
      <p class="fine">Shipping and tax calculated at checkout. Free over {money(FREE)}.</p>
      <a class="btn btn-primary" id="cartCheckout" href="{STORE}/cart">Checkout
        <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      <p class="fine">Checkout is handled by LusterLux&rsquo;s secure store. This demo never sees payment details.</p>
      <a class="tlink" href="/collections/">Keep shopping<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
    </aside>
  </div></section>
</main>
{footer()}"""
    write("/cart/index.html", head("Your cart | LusterLux",
      meta_desc("Review your LusterLux order, adjust quantities and check out securely.",
                f"Free shipping over {money(FREE)}. Support Monday to Friday, 8am to 5pm."), "/cart/",
      '<meta name="robots" content="noindex,follow" />\n' + ld(crumbs(trail))) + body)


def build_nanofusion():
    trail = [("Home","/"),("NanoFusion","/pages/nanofusion/")]
    users = [by_handle[h] for h in ("luxpro-waterless-wash-detail-spray",
                                    "ceramicx-ceramic-detail-spray",
                                    "luxquick-detail-spray") if h in by_handle]
    faq = [
      ("What is NanoFusion Surface Technology?",
       "NanoFusion combines nano-polymers with high-lubricity cleaning agents. The polymers encapsulate light contaminants so they lift off the surface instead of being dragged across it, and what stays behind is a slick protective layer that enhances gloss, boosts water beading, reduces dust adhesion, and helps the vehicle stay cleaner between washes."),
      ("Does it replace a ceramic coating?",
       "No. It is a maintenance layer, not a permanent coating. CeramicX layers on top of a coating you already have; LuxPro leaves a lighter protective film with every wipe-down. Neither is a substitute for a professional install."),
      ("Is it safe on PPF, wraps and existing coatings?",
       "Yes. LuxPro, LuxQuick, LuxFoam and CeramicX all list paint, clear coat, chrome, glass, plastic trim, PPF, vinyl wraps and existing ceramic coatings among their safe surfaces."),
      ("Can I use a waterless wash on a genuinely dirty car?",
       "No, and this is the mistake that damages paint. Waterless is for light dust, pollen, fingerprints and road film. If there is grit on the panel, foam and rinse it first."),
    ]
    faq_html = "".join(f'<details class="faq-item"><summary class="faq-q">{q}<span class="pm"></span></summary><div class="faq-a">{a}</div></details>' for q, a in faq)
    body = f"""{nav('nano')}
<main id="main">
  <section class="page-head">
    <div class="wrap">{crumb_nav(trail)}
      <p class="kick">The Technology</p>
      <h1>NanoFusion <em>Surface Technology.</em></h1>
      <p class="lead">The difference between wiping a car down and actually cleaning it is whether the dirt leaves the surface or travels across it. That is the whole problem NanoFusion was built to solve.</p>
    </div>
  </section>
  <section class="sec"><div class="wrap">
    <ol class="flow">{nano_steps()}</ol>
  </div></section>
  <section class="sec alt"><div class="wrap nano-top">
    <div class="sec-head">
      <h2 class="fade">Why encapsulation <em>matters.</em></h2>
      <p class="lead fade" data-d="1">A swirl is not a scratch from something sharp. It is a piece of grit, held against the clear coat by a towel, dragged twelve inches. Multiply that by every panel, every wash, for a few years, and you get the haze you see under a gas-station light.</p>
      <p class="lead fade" data-d="2">Encapsulation attacks that mechanically, not chemically. The nano-polymer wraps each particle and holds it in suspension so the towel is riding on a layer of lubricant with the dirt trapped inside it, not pinned underneath it. Lift the towel and the dirt goes with it.</p>
      <p class="lead fade" data-d="2">What is left behind is the second half: an ultra-thin hydrophobic film. Water beads tighter and sheets off faster, dust has less to grab, and the car stays clean measurably longer between washes.</p>
    </div>
    <figure class="nano-fig fade" data-d="2">
      <img src="/assets/scene/ceramic-sm.webp?v={V}" alt="CeramicX ceramic spray held beside a green performance car" loading="lazy" decoding="async" />
      <figcaption>CeramicX &mdash; the protection layer, on its own</figcaption>
    </figure>
  </div></section>
  <section class="sec"><div class="wrap">
    <div class="sec-head"><p class="kick slide">In the bottle</p>
      <h2 class="fade" data-d="1">Where you will find it.</h2></div>
    <div class="grid four fade" data-d="2">{"".join(card(p) for p in users)}</div>
  </div></section>
  <section class="sec alt"><div class="wrap wrap-n">
    <div class="sec-head"><h2>Straight answers.</h2></div>
    <div class="faq-list">{faq_html}</div>
  </div></section>
</main>
{footer()}"""
    sch = [crumbs(trail), {"@context":"https://schema.org","@type":"FAQPage",
      "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}]
    write("/pages/nanofusion/index.html",
      head("NanoFusion Surface Technology | LusterLux",
           "How NanoFusion works: nano-polymers encapsulate dust and road film so it lifts off the paint instead of dragging across it, leaving a slick hydrophobic layer behind.",
           "/pages/nanofusion/", "\n".join(ld(s) for s in sch)) + body)


def build_about():
    trail = [("Home","/"),("Our Story","/pages/about/")]
    body = f"""{nav('about')}
<main id="main">
  <section class="page-head">
    <div class="wrap">{crumb_nav(trail)}
      <p class="kick">Built Through Experience</p>
      <h1>Four years, <em>two to ten cars a day.</em></h1>
    </div>
  </section>
  <section class="sec"><div class="wrap story-grid">
    <div class="story-copy">
      <p class="fade">Brandon and Chase did not start with a formula. They started with a rental fleet, and the daily reality of getting two to ten vehicles clean, fast, without wrecking anyone&rsquo;s paint.</p>
      <p class="fade" data-d="1">Four years of that teaches you things a lab cannot. Which tire dressings end up as a stripe down the rocker panel on the first pull-out. Which interior cleaners leave a dash you can see reflected in the windshield at sunset. Which wheel cleaners need so much scrubbing that you damage the finish getting the brake dust off. Which waterless sprays are just moving grit around.</p>
      <p class="fade" data-d="1">They knew exactly what car care products should do, and exactly what most of them were missing. So they built the line around the gaps &mdash; and they still test every formula against real vehicles, in Arizona sun, in real conditions, before it goes in a bottle.</p>
      <p class="fade" data-d="2">That is the whole story. No lab coat, no boardroom. Two people who washed a lot of cars and got tired of the products.</p>
      <p class="sign fade" data-d="2"><b>Brandon &amp; Chase</b> &middot; Founders, LusterLux</p>
      <div class="hero-ctas fade" data-d="3" style="margin-top:30px">
        <a class="btn btn-primary" href="/collections/">Shop the Line<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
        <a class="btn btn-line" href="/pages/nanofusion/">The technology</a>
      </div>
    </div>
    <figure class="story-fig fade" data-d="2">
      <img src="/assets/scene/hero-foam.webp?v={V}" alt="Washing a car with a pressure washer and LusterLux foam in a driveway" loading="lazy" decoding="async" />
    </figure>
  </div></section>
  <section class="sec bone">
    <div class="wrap">
      <div class="sec-head c">
        <p class="kick c slide">In the field</p>
        <h2 class="fade" data-d="1">Four years of <em>real vehicles.</em></h2>
      </div>
      <div class="hive small fade" data-d="2" aria-label="LusterLux at work">
        <span class="hive-word w1">Foam.</span>
        <span class="hive-word w2">Wheels.</span>
        <span class="hive-word w3">Finish.</span>
        {honeycomb([[1, 2], [3, 4, 5], [6, 7], [8, 9, 10]])}
      </div>
    </div>
  </section>
</main>
{footer()}"""
    write("/pages/about/index.html",
      head("Our Story | LusterLux",
           "LusterLux was built by Brandon and Chase after four years maintaining a rental fleet, washing two to ten vehicles a day. Car care made by detailers, in the USA.",
           "/pages/about/", ld(crumbs(trail))) + body)


def guide_card(g):
    return f"""<article class="gcard">
  <a class="gcard-fig" href="/blogs/guides/{g['slug']}/" tabindex="-1" aria-hidden="true">
    <img src="/assets/scene/{g['img']}-sm.webp?v={V}" alt="{esc(plain(g['title']))}" loading="lazy" decoding="async" /></a>
  <div class="gcard-body">
    <p class="gcard-cat">{g['cat']} &middot; {g['read']} min read</p>
    <h3><a href="/blogs/guides/{g['slug']}/">{g['title']}</a></h3>
    <p>{g['dek']}</p>
  </div>
</article>"""


def build_guides():
    trail = [("Home", "/"), ("Guides", "/blogs/guides/")]
    cards = "".join(guide_card(g) for g in GUIDES)
    body = f"""{nav('guides')}
<main id="main">
  <section class="page-head"><div class="wrap">{crumb_nav(trail)}
    <p class="kick">Guides</p>
    <h1>How to actually <em>do the job.</em></h1>
    <p class="lead">Written by people who washed two to ten vehicles a day for four years. No filler, no affiliate padding &mdash; just the steps, the order, and the mistakes that cost you paint.</p>
  </div></section>
  <section class="sec"><div class="wrap">
    <div class="grid three">{cards}</div>
  </div></section>
</main>
{footer()}"""
    write("/blogs/guides/index.html", head("Car Care Guides | LusterLux",
      meta_desc("Detailing guides from the people who washed a rental fleet for four years: waterless washing, foam ratios, tire browning, faded trim, golf carts and desert heat.",
                "No filler."), "/blogs/guides/",
      "\n".join(ld(s) for s in [crumbs(trail),
        {"@context":"https://schema.org","@type":"CollectionPage","name":"Car Care Guides",
         "url":SITE+"/blogs/guides/","isPartOf":{"@type":"WebSite","name":"LusterLux","url":SITE+"/"},
         "mainEntity":{"@type":"ItemList","itemListElement":[
           {"@type":"ListItem","position":i+1,"name":g["title"],
            "url":SITE+f'/blogs/guides/{g["slug"]}/'} for i,g in enumerate(GUIDES)]}}])) + body)

    for i, g in enumerate(GUIDES):
        url = f'/blogs/guides/{g["slug"]}/'
        gt = [("Home","/"),("Guides","/blogs/guides/"),(g["title"], url)]
        prods = [by_handle[h] for h in g["products"] if h in by_handle]
        pcards = "".join(card(p) for p in prods)
        faq = "".join(f'<details class="faq-item"><summary class="faq-q">{q}<span class="pm"></span></summary>'
                      f'<div class="faq-a">{a}</div></details>' for q, a in g["faq"])
        more = "".join(guide_card(x) for x in (GUIDES[i+1:] + GUIDES[:i])[:2])
        steps = "".join(f"<li>{s}</li>" for s in g["how"])
        sch = [crumbs(gt),
          {"@context":"https://schema.org","@type":"Article","headline":g["title"],
           "description":g["dek"],"url":SITE+url,
           "image":SITE+f'/assets/scene/{g["img"]}.webp',
           "author":{"@type":"Organization","name":"LusterLux"},
           "publisher":{"@id":SITE+"/#org"},
           "mainEntityOfPage":{"@type":"WebPage","@id":SITE+url}},
          {"@context":"https://schema.org","@type":"HowTo","name":g["title"],
           "description":g["dek"],
           "step":[{"@type":"HowToStep","position":n+1,"text":plain(s)} for n,s in enumerate(g["how"])],
           "supply":[{"@type":"HowToSupply","name":p["title"]} for p in prods]},
          {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
            {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":plain(a)}}
            for q,a in g["faq"]]}]
        b = f"""{nav('guides')}
<main id="main">
  <article>
  <section class="page-head"><div class="wrap wrap-n">{crumb_nav(gt)}
    <p class="kick">{g['cat']} &middot; {g['read']} min read</p>
    <h1>{g['title']}</h1>
    <p class="lead">{g['dek']}</p>
  </div></section>
  <figure class="gfig"><div class="wrap">
    <img src="/assets/scene/{g['img']}.webp?v={V}" alt="{esc(g['alt'])}" loading="lazy" decoding="async" />
  </div></figure>
  <section class="sec gbody"><div class="wrap wrap-n">
    <div class="tldr"><h2>The short version</h2><ol class="steps-num">{steps}</ol></div>
    {md(g['body'])}
  </div></section>
  <section class="sec alt"><div class="wrap wrap-n">
    <div class="sec-head"><h2>Questions.</h2></div>
    <div class="faq-list">{faq}</div>
  </div></section>
  </article>
  <section class="sec"><div class="wrap">
    <div class="sec-head"><p class="kick slide">What this uses</p>
      <h2 class="fade" data-d="1">Products in this guide.</h2></div>
    <div class="grid four fade" data-d="2">{pcards}</div>
  </div></section>
  <section class="sec alt"><div class="wrap">
    <div class="sec-head"><h2>Keep reading.</h2></div>
    <div class="grid three" style="margin-top:28px">{more}</div>
  </div></section>
</main>
{footer()}"""
        write(url + "index.html", head(f'{g["title"]} | LusterLux',
              meta_desc(g["dek"], f'A LusterLux guide. {g["read"]} minute read.'),
              url, "\n".join(ld(s) for s in sch),
              og_img=f'/assets/scene/{g["img"]}.webp') + b)


def build_community():
    trail = [("Home","/"),("Community","/pages/community/")]
    socials = [("Instagram","https://www.instagram.com/lusterluxauto/","Build shots, product drops and the occasional customer car that stops us."),
               ("TikTok","https://www.tiktok.com/@lusterluxauto","Short-form: foam, before-and-afters, and the two-minute version of most of our guides."),
               ("YouTube","https://www.youtube.com/@lusterluxauto","Longer walkthroughs and full details, start to finish."),
               ("Facebook","https://www.facebook.com/lusterluxauto","Where the longer conversations and questions happen.")]
    cards = "".join(f"""<a class="soc" href="{u}" target="_blank" rel="noopener">
      <h3>{n}<svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M9 7h8v8"/></svg></h3>
      <p>{d}</p></a>""" for n, u, d in socials)
    body = f"""{nav('community')}
<main id="main">
  <section class="page-head"><div class="wrap">{crumb_nav(trail)}
    <p class="kick">Community</p>
    <h1>Show us <em>the car.</em></h1>
    <p class="lead">The best part of this is seeing what people do with it. Tag us and we will share it &mdash; daily drivers, project cars, carts, boats, work trucks. All of it counts.</p>
  </div></section>
  <section class="sec"><div class="wrap">
    <div class="soc-grid">{cards}</div>
  </div></section>
  <section class="sec alt"><div class="wrap">
    <div class="sec-head"><p class="kick slide">Talk to us</p>
      <h2 class="fade" data-d="1">Brandon and Chase <em>answer their own phones.</em></h2>
      <p class="lead fade" data-d="2">Not a support queue. If you have a question about what to use on something, ask the people who made it.</p></div>
    <div class="contact-grid fade" data-d="2">
      <a class="contact" href="mailto:support@lusterluxauto.com"><span>Email</span><b>support@lusterluxauto.com</b></a>
      <a class="contact" href="tel:+14804169665"><span>Brandon</span><b>480-416-9665</b></a>
      <a class="contact" href="tel:+14808481453"><span>Chase</span><b>480-848-1453</b></a>
      <p class="contact"><span>Hours</span><b>Mon&ndash;Fri, 8am&ndash;5pm</b></p>
    </div>
  </div></section>
</main>
{footer()}"""
    write("/pages/community/index.html", head("Community | LusterLux",
      meta_desc("Tag LusterLux and we will share it. Instagram, TikTok, YouTube and Facebook, plus direct lines to Brandon and Chase if you have a question about what to use."),
      "/pages/community/", ld(crumbs(trail))) + body)


def build_redirects():
    """301 map from the current Shopify URLs to this architecture."""
    rows = [("# from", "to", "note")]
    raw = json.load(open(os.path.join(ROOT, "tools", "products.raw.json")))["products"]
    live = {p["handle"] for p in raw}
    for p in raw:
        h = p["handle"]
        if h in by_handle:
            continue                                   # unchanged
        base = re.sub(r"-(show|copy)$", "", h)
        # a couple of the duplicates were created from a differently-named original
        ALIAS = {"luxfoam-foam-soap": "luxfoam-foam-cannon-soap"}
        base = ALIAS.get(base, base)
        target = by_handle[base]["url"] if base in by_handle else "/collections/"
        note = "trade-show duplicate — undercuts retail pricing, de-index" if h.endswith(("-show", "-copy")) else "removed"
        rows.append((f"/products/{h}", target, note))
    for h, p in by_handle.items():
        if h.endswith("-1"):
            rows.append((f"/products/{h[:-2]}", p["url"], "clean handle — rename target, -1 currently 404s"))
    old_cols = {
      "starter-kits":"/collections/kits-systems/","interior-essentials":"/collections/interior/",
      "interior-tools":"/collections/towels-tools/","exterior-essentials":"/collections/wash-waterless/",
      "rims-and-tires-essentials":"/collections/wheels-tires/","ceramic-essentials":"/collections/wash-waterless/",
      "drying-essentials":"/collections/towels-tools/","premium-towel-essentials":"/collections/towels-tools/",
      "golfcart-care":"/collections/beyond-the-car/","boat-care":"/collections/beyond-the-car/",
      "off-road-care-coming-soon":"/collections/beyond-the-car/","kits":"/collections/kits-systems/",
      "all":"/collections/"}
    for old, new in old_cols.items():
        rows.append((f"/collections/{old}", new, '"Essentials" retired' if "essential" in old else "renamed"))
    rows.append(("/collections/starter-kits/Everything-for-the-Perfect-Waterless-Wash.",
                 "/collections/kits-systems/", "broken tag filter with trailing period — crawl garbage"))
    rows.append(("/pages/why-lusterlux", "/pages/nanofusion/", "merged"))
    rows.append(("/pages/built-ahead-of-the-industry", "/pages/nanofusion/", "merged"))
    rows.append(("/pages/lusterlux-community", "/pages/community/", "renamed"))
    rows.append(("/pages/contact", "/pages/community/", "contact lives with community"))
    rows.append(("/pages/faq", "/pages/nanofusion/", "FAQs now sit on the pages they answer"))
    rows.append(("/blogs/news", "/blogs/guides/", "blog is empty — repoint to guides"))
    out = "\n".join(",".join(r) for r in rows) + "\n"
    write("/redirects.csv", out)
    return len(rows) - 1


def build_meta_files():
    urls = ["/", "/collections/", "/cart/", "/pages/find-your-product/",
            "/pages/nanofusion/", "/pages/about/"]
    urls += [f'/collections/{g["k"]}/' for g in GROUPS]
    urls += [f'/collections/{s["k"]}/' for s in SUBS]
    urls += ["/collections/merch/"]
    urls += [f'/collections/{w["k"]}/' for w in WORLDS]
    urls += [p["url"] for p in P]
    urls += [f"/pages/find-your-product/{s}-{j}/" for s, _, _ in SURFACES for j, _ in JOBS]
    urls += ["/blogs/guides/", "/pages/community/"]
    urls += [f'/blogs/guides/{g["slug"]}/' for g in GUIDES]
    seen, out = set(), []
    for u in urls:
        if u in seen: continue
        seen.add(u)
        pri = "1.0" if u == "/" else ("0.8" if u.startswith("/collections") or u.startswith("/products") else "0.6")
        out.append(f"  <url><loc>{SITE}{u}</loc><priority>{pri}</priority></url>")
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "\n".join(out) + "\n</urlset>\n")
    write("/robots.txt", f"User-agent: *\nDisallow: /cart/\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    return len(seen)


if __name__ == "__main__":
    for d in ("collections", "products", "pages", "cart", "blogs"):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    build_home(); build_collections(); build_products()
    build_finder(); build_cart(); build_nanofusion(); build_about()
    build_guides(); build_community()
    r = build_redirects()
    n = build_meta_files()
    print(f"  redirects.csv   {r} rules")
    pages = sum(len(f) for _, _, f in os.walk(ROOT) for f in [[x for x in f if x == "index.html"]])
    print(f"built {n} routes")
    for d in ("collections", "products", "pages", "blogs"):
        c = sum(1 for _, _, fs in os.walk(os.path.join(ROOT, d)) for f in fs if f == "index.html")
        print(f"  /{d:<13} {c} pages")
