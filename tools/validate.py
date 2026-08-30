#!/usr/bin/env python3
"""Site-wide checks. Run after build-site.py; exits non-zero on any failure."""
import json, os, re, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAN = ["premium", "luxury", "luxurious", "flawless", "showroom-quality",
       "unmatched", "top-tier", "ultimate"]
# Copy we do not police: legal/spec strings and the brand's own product names.
BAN_SKIP = re.compile(r"(luxpro|lusterlux|luster lux)", re.I)

pages = []
for dp, dn, fn in os.walk(ROOT):
    # anchor at the repo root — "collections/tools" is a real page, "tools/" is not
    rel_dir = os.path.relpath(dp, ROOT)
    if rel_dir.split(os.sep)[0] in ("archive", "tools", "assets", "data", ".git"):
        continue
    for f in fn:
        if f.endswith(".html"):
            pages.append(os.path.join(dp, f))
pages.sort()

fails, warns = [], []
def bad(p, m): fails.append(f"{os.path.relpath(p, ROOT)}: {m}")
def warn(p, m): warns.append(f"{os.path.relpath(p, ROOT)}: {m}")

titles, descs, canons = Counter(), Counter(), {}
all_hrefs = set()

VOID = {"img", "br", "hr", "input", "meta", "link", "source", "use", "path", "area"}

class Imgs(HTMLParser):
    """alt="" is correct on a decorative image — one marked aria-hidden, or one
       inside a wrapper that already carries the accessible name (aria-hidden or
       aria-label). Only flag images that are genuinely unlabelled, and flag a
       missing alt attribute anywhere."""
    def __init__(self):
        super().__init__(); self.bad = []; self.n = 0; self.stack = []
    def handle_starttag(self, tag, a):
        d = dict(a)
        if tag == "img":
            self.n += 1
            alt = d.get("alt")
            covered = (d.get("aria-hidden") == "true") or any(self.stack)
            if alt is None:
                self.bad.append(("no alt attribute", d.get("src", "?")))
            elif not alt.strip() and not covered:
                self.bad.append(('alt="" and not decorative', d.get("src", "?")))
            return
        if tag in VOID: return
        self.stack.append(d.get("aria-hidden") == "true" or bool(d.get("aria-label")))
    def handle_endtag(self, tag):
        if tag not in VOID and self.stack: self.stack.pop()

for p in pages:
    h = open(p, encoding="utf-8").read()
    rel = os.path.relpath(p, ROOT)

    t = re.search(r"<title>(.*?)</title>", h, re.S)
    if not t: bad(p, "no <title>")
    else:
        tt = t.group(1).strip(); titles[tt] += 1
        if not 15 <= len(tt) <= 65: warn(p, f"title {len(tt)} chars")
        if "&amp;amp;" in tt: bad(p, "double-escaped title")

    d = re.search(r'<meta name="description" content="(.*?)"', h, re.S)
    if not d: bad(p, "no meta description")
    else:
        dd = d.group(1).strip(); descs[dd] += 1
        if not 70 <= len(dd) <= 165: warn(p, f"description {len(dd)} chars")

    n_h1 = len(re.findall(r"<h1\b", h))
    if n_h1 != 1: bad(p, f"{n_h1} h1 tags")

    c = re.search(r'<link rel="canonical" href="(.*?)"', h)
    if not c: bad(p, "no canonical")
    else: canons[c.group(1)] = canons.get(c.group(1), 0) + 1
    if not re.search(r'<meta property="og:image"', h): bad(p, "no og:image")

    for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try: json.loads(blob)
        except Exception as e: bad(p, f"invalid JSON-LD: {e}")

    text = re.sub(r"<(script|style)\b.*?</\1>", " ", h, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    for w in BAN:
        for m in re.finditer(rf"\b{re.escape(w)}\b", text, re.I):
            ctx = text[max(0, m.start()-12):m.end()+12]
            if not BAN_SKIP.search(ctx): bad(p, f'banned word "{w}" near "{ctx.strip()}"')

    ip = Imgs(); ip.feed(h)
    for why, src in ip.bad: bad(p, f"{why}: {src}")

    for href in re.findall(r'(?:href|src)="([^"#?]+)', h):
        if href.startswith(("http", "mailto:", "tel:", "data:", "//")): continue
        all_hrefs.add((p, href))

for tt, n in titles.items():
    if n > 1: fails.append(f'duplicate title x{n}: "{tt}"')
for dd, n in descs.items():
    if n > 1: fails.append(f'duplicate description x{n}: "{dd}"')
for cc, n in canons.items():
    if n > 1: fails.append(f"duplicate canonical x{n}: {cc}")

for p, href in sorted(all_hrefs):
    tgt = os.path.normpath(os.path.join(ROOT, href.lstrip("/"))) if href.startswith("/") \
          else os.path.normpath(os.path.join(os.path.dirname(p), href))
    if os.path.isdir(tgt): tgt = os.path.join(tgt, "index.html")
    if not os.path.exists(tgt): bad(p, f"broken link -> {href}")

sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
sm_locs = {re.sub(r"^https?://[^/]+", "", u) for u in re.findall(r"<loc>(.*?)</loc>", sm)}
page_urls = set()
for p in pages:
    r = "/" + os.path.relpath(p, ROOT).replace("index.html", "")
    page_urls.add(r if r.endswith("/") else r)
missing = page_urls - sm_locs - {"/404.html"}
extra = sm_locs - page_urls
for u in sorted(missing): fails.append(f"page not in sitemap: {u}")
for u in sorted(extra):   fails.append(f"sitemap URL has no page: {u}")

print(f"pages: {len(pages)}   sitemap: {len(sm_locs)}   links checked: {len(all_hrefs)}")
if warns:
    print(f"\nWARN ({len(warns)}):")
    for w in warns[:25]: print("  " + w)
    if len(warns) > 25: print(f"  ... +{len(warns)-25} more")
print(f"\nFAIL ({len(fails)}):" if fails else "\nFAIL: none")
for f in fails[:60]: print("  " + f)
if len(fails) > 60: print(f"  ... +{len(fails)-60} more")
sys.exit(1 if fails else 0)
