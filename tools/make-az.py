#!/usr/bin/env python3
"""Arizona desert ridge behind the founders' story.

Hand-written saguaros read as green blobs because the arms only rose ~20px
before the cap. A real saguaro's arm goes out a short way at a tight elbow then
runs UP roughly parallel to the trunk for a long stretch — the vertical rise is
most of the arm. Generated here so the proportions stay honest.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "assets", "brand", "az-ridge.svg")
W, H, GROUND = 1600, 460, 460


def saguaro(x, base, height, tw, arms, rib="rgba(0,0,0,.10)"):
    """arms: (side, start_frac, out, rise) — rise is the vertical run, and it
    dominates: that verticality is what makes it read as a saguaro."""
    top = base - height
    d = [f"M{x} {base} V{top + tw/2:.0f}"]
    for side, sf, out, rise in arms:
        y0 = base - height * sf                 # where the arm leaves the trunk
        el = tw * 0.62                          # elbow radius, kept tight
        sgn = 1 if side == "r" else -1
        xe = x + sgn * out
        d.append(
            f"M{x} {y0:.0f} h{sgn * (out - el):.0f} "
            f"a{el:.0f} {el:.0f} 0 0 {1 if side=='r' else 0} {sgn*el:.0f} -{el:.0f} "
            f"V{y0 - rise:.0f}"
        )
    body = " ".join(d)
    ribs = "".join(
        f'<path d="M{x + o:.0f} {base} V{top + tw*0.9:.0f}" stroke="{rib}" '
        f'stroke-width="{max(1.0, tw*0.055):.1f}" fill="none" stroke-linecap="round"/>'
        for o in (-tw*0.26, 0, tw*0.26))
    return (f'<g fill="none" stroke="url(#cact)" stroke-width="{tw}" '
            f'stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="{body}"/></g>{ribs}')


def prickly_pear(x, base, s):
    """Pads: overlapping ellipses on short stems."""
    pads = [(0, 0, 1.0, 0), (-0.62, -0.44, .78, -18), (0.6, -0.5, .8, 16),
            (-0.2, -1.02, .62, -6), (0.44, -1.12, .56, 12)]
    out = ""
    for dx, dy, sc, rot in pads:
        cx, cy = x + dx*s, base - s*0.62 + dy*s
        out += (f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{s*0.34*sc:.0f}" '
                f'ry="{s*0.46*sc:.0f}" fill="url(#cact)" '
                f'transform="rotate({rot} {cx:.0f} {cy:.0f})"/>')
    return out


def ocotillo(x, base, h):
    """Thin whip-like canes fanning from a common base."""
    canes = [(-34, .82), (-19, .93), (-6, 1.0), (8, .96), (22, .88), (36, .74)]
    out = ""
    for lean, f in canes:
        out += (f'<path d="M{x} {base} Q{x + lean*0.35:.0f} {base - h*f*0.55:.0f} '
                f'{x + lean:.0f} {base - h*f:.0f}" fill="none" stroke="url(#cact)" '
                f'stroke-width="4.5" stroke-linecap="round"/>')
    return out


svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     preserveAspectRatio="xMidYMax slice" role="img" aria-hidden="true">
  <defs>
    <linearGradient id="far" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#B9A992" stop-opacity=".50"/>
      <stop offset="1" stop-color="#B9A992" stop-opacity=".16"/>
    </linearGradient>
    <linearGradient id="near" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#8A7F68" stop-opacity=".40"/>
      <stop offset="1" stop-color="#8A7F68" stop-opacity=".13"/>
    </linearGradient>
    <linearGradient id="cact" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#41660C" stop-opacity=".62"/>
      <stop offset="1" stop-color="#4E6B0A" stop-opacity=".30"/>
    </linearGradient>
  </defs>

  <path fill="url(#far)" d="M0 318 L118 262 L214 298 L330 214 L452 284 L560 242 L688 314 L800 272
    L928 326 L1048 268 L1168 314 L1288 250 L1398 300 L1508 256 L1600 304 L1600 {H} L0 {H} Z"/>
  <path fill="url(#near)" d="M0 378 L146 342 L262 372 L396 330 L520 374 L652 346 L792 382 L906 350
    L1042 384 L1182 354 L1312 386 L1452 356 L1600 380 L1600 {H} L0 {H} Z"/>

  {saguaro(232, GROUND, 268, 27, [("l", .52, 40, 96), ("r", .40, 46, 128)])}
  {saguaro(742, GROUND, 232, 23, [("r", .50, 38, 88)])}
  {saguaro(1136, GROUND, 292, 29, [("l", .44, 44, 122), ("r", .58, 40, 84)])}
  {saguaro(1470, GROUND, 196, 19, [("l", .46, 30, 70)])}
  {saguaro(556, GROUND, 176, 21, [("r", .38, 28, 62)])}
  {ocotillo(946, GROUND, 150)}
  {prickly_pear(392, GROUND, 62)}
  {prickly_pear(1298, GROUND, 48)}
</svg>
'''
open(OUT, "w").write(svg)
print(f"wrote {OUT}  ({len(svg)} bytes)")
