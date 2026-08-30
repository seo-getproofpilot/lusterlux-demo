# LusterLux — full demo site

A working concept store produced by **ProofPilot** for **LusterLux Auto Care**
(<https://lusterluxauto.com>). Static HTML/CSS/JS, generated from the live catalog.
No framework, no build toolchain.

## Run it

```bash
cd ~/lusterlux-demo && python3 -m http.server 4700
```

<http://localhost:4700/>

## It is genuinely shoppable

Add to cart works across the whole site. The cart lives in `localStorage`, survives
navigation and reloads, and **Checkout builds a Shopify cart permalink from real
variant ids** — `lusterluxauto.com/cart/<variantId>:<qty>,…` — which 302s straight
into LusterLux's live checkout with the right line items. An order placed from this
demo is a real order. Nothing here ever touches payment details.

## Routes — 76 pages

| Route | Count | What |
|---|---|---|
| `/` | 1 | Homepage |
| `/collections/` | 1 | Shop all, 43 products |
| `/collections/<category>/` | 7 | Six shop categories + merch |
| `/products/<handle>/` | 43 | Full product pages |
| `/pages/find-your-product/` | 1 | Two-question selector |
| `/pages/find-your-product/<surface>-<job>/` | 20 | Every combination, statically rendered |
| `/pages/nanofusion/` | 1 | Technology page |
| `/pages/about/` | 1 | Brand story |
| `/blogs/guides/` | 1 | Guides hub |
| `/blogs/guides/<slug>/` | 6 | Full articles, 900–1,150 words each |
| `/pages/community/` | 1 | Social + direct lines to the founders |
| `/cart/` | 1 | Full cart page (noindex) |

Plus `sitemap.xml`, `robots.txt` and `redirects.csv` — a 39-rule 301 map from the
current Shopify URLs, covering the nine trade-show duplicate product pages, the
retired "Essentials" collections, the broken tag-filter URL with the trailing period,
and the merged `/pages/*` routes.

**Routes follow Shopify's native shape** (`/products/…`, `/collections/…`) on purpose.
adamspolishes.com — the structural reference — is itself a Shopify store on exactly
these URLs (`adamspolishes.myshopify.com`). Shopify is not the constraint; the theme,
IA, metadata and content are. Building on these routes means the demo maps 1:1 onto
what LusterLux would actually ship.

## Regenerating

```bash
python3 tools/fetch-assets.py     # product cutouts + scene plates (or pass keys)
python3 tools/build-catalog.py    # data/catalog.json + data/catalog.js
python3 tools/build-site.py       # the whole page tree
```

`data/catalog.*` is **generated — never hand-edit**. The editorial layer (names,
functions, blurbs, best-for, how-to steps, pairings) lives in `tools/build-catalog.py`.
Bump `V` at the top of `build-site.py` on every build; it cache-busts every asset.

`tools/_contact.png` is a contact sheet of every cutout on a dark ground — check it
after any pipeline change. `tools/_raw/` is a ~60 MB download cache.

## Build guarantees, enforced by the validators

- 76 pages, **76 unique titles, 76 unique meta descriptions**, all 120–165 chars
- Exactly one `<h1>` per page; canonical on every page
- Zero broken internal links; sitemap matches the route list exactly
- Every `<img>` has alt text
- All JSON-LD parses: Organization, WebSite+SearchAction, ItemList, CollectionPage,
  Product (with real price + availability), AggregateRating, Article, FAQPage, HowTo,
  BreadcrumbList
- `og:image` on every page
- **Banned voice words never appear in body copy**: premium, luxury, luxurious,
  flawless, showroom-quality, unmatched, top-tier, ultimate. `build-catalog.py` fails
  loudly if one slips into the editorial layer. (They are permitted in `<title>` where
  they are search terms — the spec's own homepage title uses "Premium".)

## Scroll performance — do not undo these

The first build scrolled badly (a pause, then a lurch). In order of impact:

1. **No wheel hijacking.** Lenis was removed; its 1.35 s easing *is* the pause-then-lurch,
   and loading it from a CDN changed scroll behaviour partway through page load.
2. **No `backdrop-filter` on anything pinned during scroll.** The nav goes 98.5 % opaque
   once `.scrolled`; the category bar is fully opaque. Blur survives only on the
   transparent nav at the very top.
3. **No animated transforms inside `position: sticky` boxes that also clip and filter** —
   that re-rasterises the layer every frame. Only the hero plate is parallaxed.
4. **One drop-shadow per bottle**, with the accent glow in the stage's background gradient.
5. **Right-sized images.** Scene plates ship full-size only where they go full-bleed
   (`SCENE_FULL`); everything else uses a 900 px `-sm`. Product cutouts have a 460 px
   `-sm` for grids. Everything carries `decoding="async"`.
6. **The reveal sweep is rAF-throttled and detaches itself** once everything is revealed.

## Known CSS trap

**Percentage heights do not resolve against an `aspect-ratio` box** — a child with
`height:100%` silently falls back to intrinsic size. That is why the bottle stages use an
absolutely-positioned `.plinth` sized with flex, and `.card-fig img` is absolute with
`width/height: calc(100% - 40px)`. Note `width:auto` on an *absolutely positioned replaced
element* also falls back to intrinsic width even with all four insets set — give it an
explicit width.

## What is real and what is not

- **Real:** every product name, price, variant id, description claim, coverage figure,
  durability window, review quote, phone number and checkout link. Prices and variant ids
  come from `lusterluxauto.com/products.json`, fetched **2026-08-29**.
- **Ours:** layout, information architecture, copywriting, the product finder, the cart,
  and all structured data.
- **Nothing is invented.** No fabricated certifications, durability numbers, addresses or
  review counts. No `LocalBusiness` schema — LusterLux has no published address or Google
  Business Profile, and a wrong NAP is worse than none.
- Both footers carry a dashed note saying this is a ProofPilot concept and the product and
  photography belong to LusterLux.

## Two corrections to the original audit

**The `-1` handles are not duplicates.** All ten are the only version of that product —
`/products/waterless-wash-system` and `/products/complete-detail-system` both return 404.
Nothing to merge. `redirects.csv` treats them as a handle rename with a 301, not a merge.

**The real duplicate-content problem is the nine "(Show)" products** — genuine second
product pages for existing SKUs at trade-show pricing (LuxFoam at $17.99 against $19.99
retail), plus a `luxquick-detail-spray-copy`. They are live and indexable, so they split
ranking signal *and* publicly undercut retail. All ten are excluded here and 301'd in
`redirects.csv`.

## Still open

- **Trail Foam** is a $0, sold-out product on the live store. It appears in Beyond the Car
  as a coming-soon card rather than a purchasable dead end, and is excluded from nav and
  from `Product` schema availability as InStock. If LusterLux wants a waitlist there,
  that is a small addition.
- **No `LocalBusiness` schema.** No published address, no Google Business Profile.
- **Merch is two SKUs**, so it lives in the footer and `/collections/merch/` rather than
  top-level nav.
