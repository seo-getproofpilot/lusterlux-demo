#!/usr/bin/env python3
"""
LusterLux — catalog builder.

Merges the live Shopify catalog (tools/products.raw.json) with a hand-written
editorial layer and emits data/catalog.json + data/catalog.js.

Rules that must hold:
  * price, title, variant id and product URL always come from the live store
  * every claim in desc / bestFor / coverage traces to LusterLux's own copy
  * names use the em-dash pattern:  Name — Function
  * banned voice words never appear: premium, luxury, luxurious, flawless,
    showroom-quality, unmatched, top-tier, ultimate
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "tools", "products.raw.json")
STORE = "https://lusterluxauto.com"

CATS = [
  ("wash-waterless", "Wash &amp; Waterless", "Foam it, wash it, or skip the hose entirely — plus the ceramic layer that goes on after."),
  ("wheels-tires",   "Wheels &amp; Tires",   "Brake dust off, sidewalls back to black, nothing slung down the side of your car."),
  ("interior",       "Interior",             "Dash, console, trim and cabin air. Clean finishes, no gloss, no greasy film."),
  ("towels-tools",   "Towels &amp; Tools",   "The microfiber, brushes, cannons and buckets the chemistry was built around."),
  ("beyond-the-car", "Beyond the Car",       "Golf carts, boats and anything that comes home covered in trail dust."),
  ("kits-systems",   "Kits &amp; Systems",   "Start with one bottle or take the whole bay. Every system is a real discount on the parts."),
]
MERCH = ("merch", "Merch", "Wear it.")

BANNED = re.compile(r"\b(premium|luxur(y|ious)|flawless|showroom[- ]quality|unmatched|top[- ]tier|ultimate)\b", re.I)

# ---- editorial layer -------------------------------------------------------
# fn      = function, becomes the second half of "Name — Function"
# line    = the one-line hook, brand voice
# short   = card / grid blurb
# desc    = product page paragraph
# bestFor = surfaces, taken from the product's own safe-surface list
# how     = 3-5 steps, from the bottle directions
# pairs   = handles of 1-2 products it genuinely works with
# specs   = short chips for the showcase
E = {
 "luxpro-waterless-wash-detail-spray": dict(
   cat="wash-waterless", acc="#ff5cb8", img="luxpro", hero=1, size="16 oz",
   n="LuxPro", fn="Waterless Wash", line="Skip the hose. Keep the shine.",
   short="Nano-polymers wrap the dust so it lifts off the paint instead of dragging across it. No bucket, no hose, no driveway.",
   desc="LuxPro is the bottle NanoFusion was built for. Advanced nano-polymers encapsulate light dust, pollen, fingerprints and road film so they lift away from the surface rather than getting dragged across it, while a high-lubricity carrier keeps the towel gliding. What stays behind is a slick, hydrophobic layer that adds gloss, tightens water beading and keeps the next round of dust from taking hold. It is the difference between wiping a car down and actually cleaning it.",
   bestFor=["Paint &amp; clear coat","Glass","Chrome","Plastic trim","Wheels","PPF","Vinyl wrap","Ceramic coatings"],
   how=["Shake well before each use.","Work one panel at a time, out of direct sun.","Mist a light, even coat onto the surface.","Wipe in one direction with a clean Edgeless Lux towel.","Flip to a dry side and buff off the haze."],
   pairs=["3-pack-edgeless-lux-edgeless-microfiber-towels","ceramicx-ceramic-detail-spray"],
   coverage="15–30 vehicles per bottle",
   specs=["NanoFusion Technology","Encapsulating Formula","15–30 Vehicles Per Bottle","Safe On PPF, Wraps &amp; Ceramic"]),

 "ceramicx-ceramic-detail-spray": dict(
   cat="wash-waterless", acc="#4fc3f7", img="ceramicx", hero=2, size="16 oz",
   n="CeramicX", fn="Ceramic Spray", line="Bonded protection, one panel at a time.",
   short="A ceramic layer in the time it takes to wipe a panel. Hard water beading, real gloss depth, and a surface that stays clean longer.",
   desc="CeramicX bonds to the surface and leaves a durable, hydrophobic layer that repels water, road grime and UV. Gloss goes up, dirt has less to grab, and the next wash takes half as long. It layers on top of a coating you already have rather than replacing it, so it works as both a standalone protectant and a topper between full ceramic services.",
   bestFor=["Paint &amp; clear coat","Chrome","Plastic trim","Glass","PPF","Existing ceramic coatings"],
   how=["Start with a clean, dry, cool surface.","Mist two to three sprays per panel.","Spread evenly with an Edgeless Lux towel.","Flip to a dry towel and buff until it disappears.","Give it an hour before it sees rain."],
   pairs=["luxpro-waterless-wash-detail-spray","3-pack-edgeless-lux-edgeless-microfiber-towels"],
   coverage="10–20 vehicles per bottle · up to 8 months of protection",
   specs=["Up To 8 Months Protection","Extreme Hydrophobics","10–20 Vehicles Per Bottle","Layers Over Existing Coatings"]),

 "luxfoam-foam-cannon-soap": dict(
   cat="wash-waterless", acc="#6a4cf0", img="luxfoam", hero=3, size="16 oz",
   n="LuxFoam", fn="Foam Soap", line="Let the foam do the scrubbing.",
   short="Thick, clinging foam that lifts the grit before your mitt ever touches the paint — the single biggest thing standing between a wash and a swirl.",
   desc="LuxFoam throws rich foam that clings long enough to actually break down road film instead of sliding straight off. High lubricity means the mitt glides rather than grabs, and dirt stays encapsulated in the suds where it cannot cut into the clear coat. It rinses clean with no residue and will not strip the wax, sealant or coating already on the car.",
   bestFor=["Paint &amp; clear coat","Chrome","Glass","Plastic trim","PPF","Vinyl wrap","Ceramic coatings"],
   how=["Rinse the car down first — never foam a dry, dusty panel.","Fill the cannon and dial in a thick mix.","Blanket the vehicle top to bottom and let it dwell.","Wash with a LuxMit, top panels first, rinsing the mitt often.","Rinse fully and dry with a LuxTowel."],
   pairs=["luxcannon-foam-cannon","luxmit-wash-mit"],
   coverage="8–16 washes per bottle",
   specs=["High-Lubricity Wash","8–16 Washes Per Bottle","Coating &amp; Wax Safe","Cannon Or Two-Bucket"]),

 "luxwheelassassin-wheel-cleaner": dict(
   cat="wheels-tires", acc="#e3d92a", img="wheelassassin", hero=4, size="16 oz",
   n="LuxWheelAssassin", fn="Wheel Cleaner", line="Attack the brake dust. Leave the finish alone.",
   short="Fast-acting on bonded brake dust, grease and road film, so the barrel comes clean with a fraction of the scrubbing.",
   desc="Brake dust is not dirt — it is hot metal fused into your finish, and scrubbing it is how wheels get ruined. LuxWheelAssassin breaks it down chemically so it releases with minimal agitation, then rinses away clean. Safe on clear-coated, painted, chrome, alloy and factory wheels, which covers virtually everything short of bare polished aluminium.",
   bestFor=["Clear-coated wheels","Painted wheels","Chrome","Alloy","Factory finishes"],
   how=["Work on cool wheels, out of direct sun.","Spray the face and the barrel until wet.","Let it dwell — do not let it dry.","Agitate with a Lux Wheel Brush where buildup is heavy.","Rinse thoroughly, then dry before dressing the tires."],
   pairs=["lux-wheel-brush","tirevenom-tire-dressing"],
   coverage="12–20 vehicles per bottle",
   note="Always test an inconspicuous area first.",
   specs=["Dissolves Brake Dust","12–20 Vehicles Per Bottle","Clear-Coat, Chrome &amp; Alloy Safe","Minimal Agitation"]),

 "tirevenom-tire-dressing": dict(
   cat="wheels-tires", acc="#c8763a", img="tirevenom", hero=5, size="16 oz",
   n="TireVenom", fn="Tire Dressing", line="Deep black that stays on the tire.",
   short="A no-sling dressing that dries to the touch. Even, dark sidewalls — and none of it flung down your paint on the first pull-out.",
   desc="Most tire shine is silicone that never really dries, which is why it ends up in a stripe along your rocker panel. TireVenom dries to the touch and stays where you put it. It restores faded rubber to a deep, even finish and shields it against UV, cracking and browning, without the greasy film that attracts dust the moment you park.",
   bestFor=["Tires &amp; sidewalls","Rubber trim","Wheel wells"],
   how=["Scrub the sidewall clean first — dressing over old dressing is what causes browning.","Let the tire dry completely.","Apply an even coat with an XPad applicator.","Level it out so there are no heavy spots.","Let it set before you drive."],
   pairs=["2-pack-xpad-applicator-pad","lux-tire-brush"],
   coverage="30–50 tires per bottle · up to 3 months",
   specs=["No-Sling, Dries To Touch","Up To 3 Months","30–50 Tires Per Bottle","UV &amp; Cracking Defense"]),

 "interiorx-interior-cleaner": dict(
   cat="interior", acc="#5fa8c9", img="interiorx", hero=6, size="16 oz",
   n="InteriorX", fn="Interior Cleaner", line="Clean cabin. No gloss, no glare.",
   short="Lifts fingerprints, spills and everyday grime off dash, console and door cards — then leaves, with no slick residue and nothing reflecting in your windshield.",
   desc="Interior cleaner is the easiest place to make a car look worse. Anything that leaves shine puts glare in your windshield and turns your steering wheel slippery. InteriorX pulls dirt, dust, fingerprints and spills off the surface and dries to a factory matte, so the cabin reads clean rather than coated.",
   bestFor=["Dashboards","Door panels","Center consoles","Steering wheels","Vinyl","Plastic","Rubber"],
   how=["Spray onto a MicroLux towel, not directly onto the panel.","Work one section at a time.","Wipe, then follow with a dry side of the towel.","Use a LuxBrush for vents, seams and switchgear."],
   pairs=["5-pack-microlux-microfiber-towels","lux-brush-interior-brush"],
   coverage="15–25 vehicles per bottle",
   specs=["Zero Greasy Residue","Factory Matte Finish","15–25 Vehicles Per Bottle","Dash, Vinyl, Plastic &amp; Rubber"]),

 "luxquick-detail-spray": dict(
   cat="wash-waterless", acc="#3fc85f", img="luxquick", size="16 oz",
   n="LuxQuick", fn="Detail Spray", line="The between-washes reset.",
   short="Pulls light dust, fingerprints and fresh water spots, then leaves a slick layer that keeps the next round from sticking.",
   desc="The car is clean, then it sits for four days and it is not. LuxQuick handles that gap. It removes light dust, fingerprints, smudges and fresh water spots, boosts gloss, and leaves enough slickness behind that the surface stays cleaner longer. It is also what you keep in the trunk on show day.",
   bestFor=["Paint &amp; clear coat","Glass","Chrome","Plastic trim","PPF","Vinyl wrap","Ceramic coatings"],
   how=["Only use it on a lightly soiled surface — never on grit.","Mist one panel at a time.","Wipe with a clean Edgeless Lux towel.","Buff with a dry side until it is streak-free."],
   pairs=["3-pack-edgeless-lux-edgeless-microfiber-towels","luxpro-waterless-wash-detail-spray"],
   coverage="15–25 vehicles per bottle",
   specs=["Streak-Free Gloss","15–25 Vehicles Per Bottle","Safe On Glass &amp; Trim","Show-Day Touch Up"]),

 "restorx-rvp-plastic-dressing": dict(
   cat="interior", acc="#d4a53c", img="restorx", size="16 oz",
   n="RestorX", fn="RVP Dressing", line="Bring the trim back. Keep it there.",
   short="Rubber, vinyl and plastic returned to factory — trim, dash, engine bay — with an even finish that never feels oily or pulls dust.",
   desc="Faded grey trim is what makes a clean car still look old. RestorX restores rubber, vinyl and plastic to an even, factory-looking finish and holds it with real UV protection — up to 6 months on exterior trim, up to 8 months inside. It levels out rather than sitting on top, so nothing feels greasy and nothing collects dust.",
   bestFor=["Exterior trim","Dashboards","Door panels","Engine bay plastics","Tires","Rubber seals"],
   how=["Clean and dry the surface first.","Apply a thin coat with an XPad applicator.","Let it level for a minute.","Wipe back any excess with a dry towel."],
   pairs=["2-pack-xpad-applicator-pad","interiorx-interior-cleaner"],
   coverage="20–40 vehicles per bottle · up to 8 months",
   specs=["Up To 8 Months Interior","Up To 6 Months Exterior","20–40 Vehicles Per Bottle","Never Oily"]),

 "newcarember-air-freshener": dict(
   cat="interior", acc="#f58cb8", img="newcarember", size="4 oz",
   n="NewCarEmber", fn="Air Freshener", line="That first-drive smell, on demand.",
   short="Neutralises what is actually in the cabin instead of layering over it, then holds a clean new-car note that never turns sweet.",
   desc="Most cabin sprays are perfume over the problem. NewCarEmber neutralises the odour at the source first, then leaves a clean, crisp new-car scent that lasts without going cloying by day three.",
   bestFor=["Cabin air","Carpet &amp; upholstery","Vents"],
   how=["Air the cabin out first.","Two or three sprays into the footwells.","One short burst into the vents with the fan running."],
   pairs=["vanillaember-air-freshener","interiorx-interior-cleaner"],
   specs=["Odor Eliminating","Long-Lasting","Never Overpowering"]),

 "vanillaember-air-freshener": dict(
   cat="interior", acc="#f2762a", img="vanillaember", size="4 oz",
   n="VanillaEmber", fn="Air Freshener", line="Warm vanilla, none of the cheap sweetness.",
   short="Smooth warm vanilla over the same odour-neutralising base — a cabin that smells cared for, not perfumed.",
   desc="Same neutralising base as NewCarEmber, different finish. A smooth, warm vanilla that reads as a clean interior rather than an air freshener hanging off the mirror.",
   bestFor=["Cabin air","Carpet &amp; upholstery","Vents"],
   how=["Air the cabin out first.","Two or three sprays into the footwells.","One short burst into the vents with the fan running."],
   pairs=["newcarember-air-freshener","interiorx-interior-cleaner"],
   specs=["Odor Eliminating","Long-Lasting","Never Overpowering"]),

 "birdielux-golf-cart-exterior-cleaner": dict(
   cat="beyond-the-car", acc="#8a76e8", img="birdielux", size="16 oz",
   n="BirdieLux", fn="Golf Cart Cleaner", line="A clean cart without a hose on the course.",
   short="Built for cart paint, plastic body panels and trim — waterless, streak-free, and it fits in the basket.",
   desc="Carts get the same dust, pollen and cart-path film a car does, and almost nowhere to wash them. BirdieLux cleans painted panels, plastic bodywork and trim waterlessly, lifting grime without streaking, so a cart can be cleaned where it sits.",
   bestFor=["Cart paint","Plastic body panels","Trim","Windshields"],
   how=["Work one panel at a time.","Mist an even coat.","Wipe with a clean Edgeless Lux towel.","Buff dry with a fresh side."],
   pairs=["xfresh-golf-cart-interior-cleaner","3-pack-edgeless-lux-edgeless-microfiber-towels"],
   specs=["Waterless","Painted &amp; Plastic Panels","Streak-Free","Cart-Specific"]),

 "xfresh-golf-cart-interior-cleaner": dict(
   cat="beyond-the-car", acc="#3fc9b0", img="xfresh", size="16 oz",
   n="XFresh", fn="Cart Interior Cleaner", line="Seats you can actually sit on.",
   short="Cleans cart seats, dash and trim without the greasy film that turns every seat into a slide.",
   desc="Cart seats live outdoors and take sunscreen, sweat and grass all season. XFresh cleans the vinyl, dash and trim and dries clean — no slick residue, which matters a lot more on a bench seat with no belts.",
   bestFor=["Cart seats","Dash &amp; trim","Vinyl","Plastic"],
   how=["Spray onto a towel, not the seat.","Work one section at a time.","Wipe and follow with a dry side.","Use a LuxBrush on textured vinyl."],
   pairs=["birdielux-golf-cart-exterior-cleaner","lux-brush-interior-brush"],
   specs=["Seats &amp; Trim","No Greasy Film","Cart-Specific"]),

 "luxcannon-foam-cannon":       dict(cat="towels-tools", acc="#9aa4ae", img="luxcannon", n="LuxCannon", fn="Foam Cannon",
   line="Where the thick foam comes from.",
   short="Pressure-washer foam cannon that turns LuxFoam into the clinging blanket the wash actually depends on.",
   desc="A foam cannon is not an accessory — without one, foam soap is just soap. The LuxCannon runs off a standard pressure washer, with an adjustable mix and fan so you can lay down a blanket thick enough to dwell and break down road film before anything touches the paint.",
   bestFor=["Pressure washers","Foam washing"], pairs=["luxfoam-foam-cannon-soap","luxgun-pressure-washer-gun"]),
 "luxgun-pressure-washer-gun":  dict(cat="towels-tools", acc="#9aa4ae", img="luxgun", n="LuxGun", fn="Pressure Washer Gun",
   line="Short body, full nozzle set.",
   short="Short-body pressure washer gun with a full quick-connect nozzle set — 0°, 15°, 25°, 40° and soap.",
   desc="A short-body gun with a quick-connect coupler and the full nozzle range, so you are not fighting a two-foot wand around a wheel arch. Swaps to the LuxCannon in one click.",
   bestFor=["Pressure washers"], pairs=["luxcannon-foam-cannon","luxfoam-foam-cannon-soap"]),
 "lux-bucket-car-washing-bucket":dict(cat="towels-tools", acc="#9aa4ae", img="luxbucket", n="Lux Bucket", fn="Wash Bucket",
   line="Half of a two-bucket wash.",
   short="The wash bucket, grit-guard ready — the other half of the method that keeps dirt off your paint.",
   desc="Two buckets, one soap and one rinse, is the oldest swirl-prevention trick there is and still the most effective. This is the bucket, sized for a grit guard.",
   bestFor=["Two-bucket washing"], pairs=["luxmit-wash-mit","luxfoam-foam-cannon-soap"]),
 "3-pack-edgeless-lux-edgeless-microfiber-towels": dict(cat="towels-tools", acc="#84D019", img="edgelesslux",
   n="Edgeless Lux", fn="Exterior Microfiber, 3-Pack",
   line="The towel the formulas were built around.",
   short="Edgeless exterior microfiber — no stitched border to drag across a panel. What LuxPro and CeramicX are meant to be used with.",
   desc="A stitched edge is a hard seam being pulled across your clear coat. These are edgeless, high-pile and exterior weight, which is why every waterless and ceramic instruction on this site says to use them.",
   bestFor=["Waterless washing","Ceramic application","Final buffing"], pairs=["luxpro-waterless-wash-detail-spray","ceramicx-ceramic-detail-spray"]),
 "5-pack-microlux-microfiber-towels": dict(cat="towels-tools", acc="#9aa4ae", img="microlux",
   n="MicroLux", fn="Interior Microfiber, 5-Pack",
   line="Interior weight, five to a pack.",
   short="Lighter-weight microfiber for glass, dash and door cards, in the quantity an interior actually takes.",
   desc="Interiors burn through towels — one for cleaner, one to dry, one for glass, and you have not done the door jambs yet. Five to a pack, interior weight, so nothing gets reused past the point of being useful.",
   bestFor=["Dash &amp; console","Glass","Door panels"], pairs=["interiorx-interior-cleaner","2-pack-luxwindow-waffle-window-towel"]),
}

# category + one-line benefit for everything else, no invented specifics
FALLBACK = {
 "luxtowel-drying-towel":        ("towels-tools", "LuxTowel", "Drying Towel", "1300 GSM, 2 ft × 3 ft plush drying towel that takes a full vehicle down in one pass."),
 "2-pack-luxwindow-waffle-window-towel": ("towels-tools", "LuxWindow", "Waffle Window Towel, 2-Pack", "Waffle weave — the only thing that leaves the inside of a windshield without haze."),
 "luxmit-wash-mit":              ("towels-tools", "LuxMit", "Wash Mitt", "Deep-pile mitt that carries lubricant and traps grit away from the paint."),
 "luxbug-bug-and-tar-remover-sponge": ("towels-tools", "LuxBug", "Bug &amp; Tar Sponge", "For the front bumper and mirror caps, safe on clear coat."),
 "2-pack-xpad-applicator-pad":   ("towels-tools", "XPad", "Applicator Pads, 2-Pack", "For laying TireVenom and RestorX down evenly instead of in streaks."),
 "lux-tire-brush":               ("wheels-tires", "Lux Tire Brush", "Stiff-Bristle Brush", "Scrubs sidewalls back to clean before anything gets dressed."),
 "lux-wheel-brush":              ("wheels-tires", "Lux Wheel Brush", "Soft Barrel Brush", "Reaches behind the spokes without marking the finish."),
 "lux-brush-interior-brush":     ("interior", "LuxBrush", "Curved Detailing Brush", "Vents, seams and the places a towel physically cannot reach."),
 "foamx-sprayer-electric-sprayer":("towels-tools", "FoamX Sprayer", "Electric Sprayer", "Even, no-pump coverage for foam and waterless work."),
 "lux-sprayer-pump-sprayer":     ("towels-tools", "Lux Sprayer", "Pump Sprayer", "Hand-pump sprayer for pre-soaking wheels and arches, and for laying down diluted product evenly without a hose or power."),
 "waterless-wash-system-1":      ("kits-systems", "NanoFusion Detail System", "Starter Kit", "LuxPro plus Edgeless Lux towels — the pairing the formula was designed around."),
 "complete-detail-system-1":     ("kits-systems", "Complete Detail System", "Kit", "Exterior through interior in one box."),
 "paint-care-system-1":          ("kits-systems", "Paint Care System", "Kit", "Wash, protect and maintain. Paint only."),
 "tire-care-system-1":           ("kits-systems", "Tire Care System", "Kit", "Clean the sidewall properly, then dress it. TireVenom with the brush and applicator that make it go on even and stay off your paint."),
 "rim-and-tire-system-kit-1":    ("kits-systems", "Rim and Tire System", "Kit", "Wheels and tires together, with the brushes for both."),
 "foam-wash-system-1":           ("kits-systems", "Foam Wash System", "Kit", "LuxFoam, the cannon and the mitt — a proper foam wash from nothing."),
 "ultimate-wash-system-1":       ("kits-systems", "Full Wash System", "Kit", "Everything the wash bay needs, foam through drying towel."),
 "complete-interior-system-1":   ("kits-systems", "Complete Interior System", "Kit", "Cleaner, dressing, brushes and towels for a full cabin reset."),
 "interior-restoration-system-1":("kits-systems", "Interior Restoration System", "Kit", "For a cabin that has been let go — restore the plastics, then hold them."),
 "dual-scent-system-1":          ("kits-systems", "Dual Scent System", "Kit", "Both Ember scents, so the cabin never runs out."),
 "towel-tantrum-kit-every-surface-every-step-every-finish": ("towels-tools", "Towel Tantrum Kit", "Every Towel Weight", "Every weight LusterLux makes — one for every surface and every step."),
 "the-platinum-system":          ("kits-systems", "The Platinum System", "Complete Kit", "Over $700 of product and accessories in one box. Every surface, every step, nothing left to buy."),
 "fairway-finish-system":        ("beyond-the-car", "FairWay Finish System", "Golf Cart Kit", "The complete cart kit — cleaners, brushes and microfiber for every surface on it."),
 "trail-foam-coming-soon":       ("beyond-the-car", "Trail Foam", "Off-Road Foam", "Foam built for mud, dust and trail film. In development."),
 "lux-t":                        ("merch", "Lux Tee", "T-Shirt", "The LusterLux tee. Soft cotton, printed mark, and the thing you will end up wearing every time you are out in the driveway."),
 "the-luxcap-limited-supply":    ("merch", "LuxCap", "Cap", "Structured cap with the LusterLux leather patch. Limited run, and when this batch is gone it is gone."),
}

# ---- vehicle worlds -------------------------------------------------------
# What you drive, not what job it does. Seeded from LusterLux's own
# golfcart-care / boat-care / off-road collections, then extended with the
# products whose own directions name those surfaces. Their live boat-care
# collection is three towels, which is not a shoppable category.
WORLDS = [
 ("car-truck", "Car &amp; Truck",
  "Daily drivers, weekend cars and work trucks. The full line applies here.",
  "hero-foam"),
 ("golf-cart", "Golf Cart",
  "Cart paint, plastic body panels and vinyl bench seats, cleaned where the cart sits.",
  "cart"),
 ("marine", "Marine",
  "Gelcoat, vinyl seating and trim take sun and salt harder than anything on the road.",
  "marine"),
 ("off-road", "Off-Road &amp; UTV",
  "Mud, trail dust and baked-on film. Same chemistry, harder job.",
  "hero-hood"),
]
# handles that belong to each world beyond the catch-all car-truck
WORLD_MEMBERS = {
 "golf-cart": ["birdielux-golf-cart-exterior-cleaner","xfresh-golf-cart-interior-cleaner",
   "fairway-finish-system","3-pack-edgeless-lux-edgeless-microfiber-towels",
   "5-pack-microlux-microfiber-towels","lux-brush-interior-brush",
   "luxwheelassassin-wheel-cleaner","tirevenom-tire-dressing","restorx-rvp-plastic-dressing",
   "luxpro-waterless-wash-detail-spray","luxquick-detail-spray","ceramicx-ceramic-detail-spray",
   "2-pack-xpad-applicator-pad","lux-tire-brush"],
 "marine": ["3-pack-edgeless-lux-edgeless-microfiber-towels","5-pack-microlux-microfiber-towels",
   "2-pack-luxwindow-waffle-window-towel","restorx-rvp-plastic-dressing",
   "ceramicx-ceramic-detail-spray","luxpro-waterless-wash-detail-spray","luxquick-detail-spray",
   "luxfoam-foam-cannon-soap","xfresh-golf-cart-interior-cleaner","luxtowel-drying-towel",
   "2-pack-xpad-applicator-pad","luxmit-wash-mit"],
 "off-road": ["trail-foam-coming-soon","luxtowel-drying-towel","luxcannon-foam-cannon",
   "5-pack-microlux-microfiber-towels","luxbug-bug-and-tar-remover-sponge","luxmit-wash-mit",
   "luxfoam-foam-cannon-soap","luxwheelassassin-wheel-cleaner","tirevenom-tire-dressing",
   "restorx-rvp-plastic-dressing","luxpro-waterless-wash-detail-spray","interiorx-interior-cleaner",
   "lux-tire-brush","lux-wheel-brush","lux-bucket-car-washing-bucket","luxgun-pressure-washer-gun",
   "rim-and-tire-system-kit-1","foam-wash-system-1"],
}
# cart- and trail-specific products are not general car care
NOT_CAR = {"birdielux-golf-cart-exterior-cleaner","xfresh-golf-cart-interior-cleaner",
           "fairway-finish-system","trail-foam-coming-soon"}

# products that also belong to Beyond the Car (cross-listed, as on the live store)
ALSO_BEYOND = ["tirevenom-tire-dressing", "restorx-rvp-plastic-dressing",
               "luxwheelassassin-wheel-cleaner", "luxfoam-foam-cannon-soap",
               "luxpro-waterless-wash-detail-spray"]

CAT_ACC = {"wash-waterless":"#6a4cf0","wheels-tires":"#c8763a","interior":"#d4a53c",
           "towels-tools":"#9aa4ae","beyond-the-car":"#8a76e8","kits-systems":"#84D019",
           "merch":"#9aa4ae"}
IMG_ALIAS = {"towel-tantrum-kit-every-surface-every-step-every-finish":"towel-tantrum-kit",
             "2-pack-luxwindow-waffle-window-towel":"2-pack-luxwindow"}


# showcase copy: hook line, body paragraph, and the beat that makes it matter.
# Every figure here is LusterLux's own -- coverage counts and durability windows
# come straight off their product pages.
SHOWCASE = {'luxpro-waterless-wash-detail-spray': ('Skip the hose. Keep the shine.', 'Most quick detailers move dirt around. LuxPro wraps it. Nano-polymers encapsulate each particle of dust, pollen and road film so it lifts clear of the panel rather than being dragged across it, while a high-lubricity carrier keeps the towel gliding on liquid instead of on your clear coat.', 'That matters because a swirl is not a scratch from something sharp — it is a grain of grit held against the paint by a towel and pulled twelve inches. Take the grit off the panel first and the swirl never happens. One 16 oz bottle does 15 to 30 vehicles.'), 'ceramicx-ceramic-detail-spray': ('Bonded protection, one panel at a time.', 'CeramicX bonds to the surface and leaves a hydrophobic layer that repels water, road grime and UV. Gloss goes up, dirt has less to grab, and the next wash takes half as long. It layers on top of a coating you already have rather than replacing it.', 'Up to eight months from one application, and 10 to 20 vehicles from a bottle. In hard-water country that layer is the difference between water beading off and water sitting on the panel long enough to leave minerals behind.'), 'luxfoam-foam-cannon-soap': ('Let the foam do the scrubbing.', 'LuxFoam throws thick foam that clings long enough to actually break down road film instead of sliding off. High lubricity means the mitt glides rather than grabs, and dirt stays encapsulated in the suds where it cannot cut into the finish.', 'Every minute the foam dwells is a minute of cleaning happening with nothing touching your paint. It rinses clean with no residue and will not strip the wax, sealant or coating already on the car. 8 to 16 washes a bottle.'), 'luxwheelassassin-wheel-cleaner': ('Attack the brake dust. Leave the finish alone.', 'Brake dust is not dirt. It is hot metal fused into your finish, and scrubbing it is how wheels get ruined. LuxWheelAssassin breaks it down chemically so it releases with minimal agitation, then rinses away clean.', 'Safe on clear-coated, painted, chrome, alloy and factory wheels, which covers virtually everything short of bare polished aluminium. 12 to 20 vehicles a bottle. Always test an inconspicuous area first.'), 'tirevenom-tire-dressing': ('Deep black that stays on the tire.', 'Most tire shine is silicone that never really dries, which is why it ends up in a stripe along your rocker panel. TireVenom dries to the touch and stays where you put it, restoring faded rubber to a deep, even finish.', 'It shields against UV, cracking and browning without the greasy film that pulls dust the moment you park. Up to three months an application, and 30 to 50 tires from a bottle.'), 'interiorx-interior-cleaner': ('Clean cabin. No gloss, no glare.', 'Interior cleaner is the easiest place to make a car look worse. Anything that leaves shine puts glare in your windshield and turns a steering wheel slippery. InteriorX pulls dirt, fingerprints and spills off the surface and dries to a factory matte.', 'Safe on dashboards, door panels, consoles, steering wheels, vinyl, plastic and rubber, and it goes 15 to 25 vehicles a bottle. The cabin reads clean rather than coated.')}

# each hero product photographed on the surface it works on; sits behind the
# cut-out bottle in the homepage showcases
IN_USE = {'luxpro-waterless-wash-detail-spray': 'use-luxpro', 'ceramicx-ceramic-detail-spray': 'use-ceramicx', 'luxfoam-foam-cannon-soap': 'use-luxfoam', 'luxwheelassassin-wheel-cleaner': 'use-wheelassassin', 'tirevenom-tire-dressing': 'use-tirevenom', 'interiorx-interior-cleaner': 'use-interiorx'}


def main():
    src = json.load(open(RAW))["products"]
    items, seen, problems = [], set(), []

    for p in src:
        h = p["handle"]
        if h.endswith("-show") or h.endswith("-copy") or h in seen:
            continue
        seen.add(h)
        v = p["variants"][0]
        ed = E.get(h)
        if ed:
            cat, name, fn, short = ed["cat"], ed["n"], ed["fn"], ed["short"]
        elif h in FALLBACK:
            cat, name, fn, short = FALLBACK[h]
            ed = {}
        else:
            problems.append("uncategorised: " + h); continue

        price = float(v["price"])
        item = {
            "h": h, "vid": str(v["id"]),
            "n": name, "fn": fn,
            "title": f"{name} — {fn}",
            "cat": cat,
            "also": ["beyond-the-car"] if h in ALSO_BEYOND else [],
            "price": price,
            "size": ed.get("size", ""),
            "acc": ed.get("acc") or CAT_ACC.get(cat, "#9aa4ae"),
            "img": ed.get("img") or IMG_ALIAS.get(h, h),
            "line": SHOWCASE.get(h, (None,))[0] or ed.get("line", ""),
            "short": short,
            "desc": ed.get("desc", short),
            "bestFor": ed.get("bestFor", []),
            "how": ed.get("how", []),
            "pairs": ed.get("pairs", []),
            "coverage": ed.get("coverage", ""),
            "note": ed.get("note", ""),
            "specs": ed.get("specs", []),
            "hero": ed.get("hero", 0),
            "inuse": IN_USE.get(h, ""),
            "showBody": SHOWCASE.get(h, (None, None, None))[1] or "",
            "showWhy": SHOWCASE.get(h, (None, None, None))[2] or "",
            "soon": price == 0,
            "storeUrl": f"{STORE}/products/{h}",
            "url": f"/products/{h}/",
        }
        for field in ("line", "short", "desc", "showBody", "showWhy"):
            if BANNED.search(item[field] or ""):
                problems.append(f"banned word in {h}.{field}: {BANNED.search(item[field]).group(0)}")
        items.append(item)

    # validate pair references resolve
    handles = {i["h"] for i in items}
    for i in items:
        for pr in i["pairs"]:
            if pr not in handles:
                problems.append(f"{i['h']} pairs with missing handle {pr}")

    items.sort(key=lambda i: (i["hero"] == 0, i["hero"], i["cat"], -i["price"]))
    for i in items:
        w = []
        if i["h"] not in NOT_CAR and i["cat"] != "merch":
            w.append("car-truck")
        for wk, members in WORLD_MEMBERS.items():
            if i["h"] in members:
                w.append(wk)
        i["worlds"] = w
    cats = [{"k": k, "t": t, "d": d} for k, t, d in CATS] + [{"k": MERCH[0], "t": MERCH[1], "d": MERCH[2]}]
    worlds = [{"k": k, "t": t, "d": d, "img": im} for k, t, d, im in WORLDS]
    payload = {"cats": cats, "worlds": worlds, "products": items,
               "meta": {"source": f"{STORE}/products.json", "fetched": "2026-08-29",
                        "freeShipping": 45.0}}

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(payload, open(os.path.join(ROOT, "data", "catalog.json"), "w"), indent=1, ensure_ascii=False)
    with open(os.path.join(ROOT, "data", "catalog.js"), "w") as f:
        f.write("/* GENERATED by tools/build-catalog.py -- do not hand-edit.\n"
                "   Titles, prices, variant ids and URLs are live LusterLux store data.\n"
                f"   Source: {STORE}/products.json  (fetched 2026-08-29) */\n"
                "window.LL = " + json.dumps(payload, ensure_ascii=False) + ";\n")

    print(f"{len(items)} products -> data/catalog.json + data/catalog.js")
    for c in cats:
        n = sum(1 for i in items if i["cat"] == c["k"])
        x = sum(1 for i in items if c["k"] in i["also"])
        print(f"  {c['k']:<16} {n}" + (f"  (+{x} cross-listed)" if x else ""))
    print("  --- worlds ---")
    for w in worlds:
        print(f"  {w['k']:<16} {sum(1 for i in items if w['k'] in i['worlds'])}")
    print("\nPROBLEMS:", *(problems or ["none"]), sep="\n  ")


if __name__ == "__main__":
    main()
