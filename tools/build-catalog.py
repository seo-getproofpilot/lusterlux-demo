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



# ---- top-level groups with real subcategories -----------------------------
# A flat list of six buckets told a new buyer nothing. This is the Adam's shape:
# five things you can hold in your head, each opening into what is actually in it.
GROUPS = [
 ("exterior", "Exterior", "Everything that touches the outside of the vehicle, in the order you use it.",
  ["wash-waterless", "wheels-tires", "ceramic"]),
 ("interior", "Interior", "Dash, trim, glass and cabin air. Clean finishes, no gloss, no greasy film.",
  ["interior-cleaners", "trim-dressings", "scents"]),
 ("tools", "Tools &amp; Towels", "The microfiber, brushes, cannons and sprayers the chemistry was built around.",
  ["microfiber", "brushes", "cannons"]),
 ("kits-systems", "Kits &amp; Systems", "Start with one bottle or take the whole bay. Every system beats the parts.",
  []),
 ("beyond-the-car", "Beyond the Car", "Golf carts, boats and anything that comes home covered in trail dust.",
  ["golf-cart", "marine", "off-road"]),
]
SUBS = [
 ("wash-waterless",   "Wash &amp; Waterless", "Foam it, wash it, or skip the hose entirely."),
 ("wheels-tires",     "Wheels &amp; Tires",   "Brake dust off, sidewalls back to black, nothing slung down your paint."),
 ("ceramic",          "Ceramic &amp; Protection", "The layer that goes on last and makes every wash after it easier."),
 ("interior-cleaners","Cleaners",           "Dash, console and door cards back to a factory matte."),
 ("trim-dressings",   "Trim &amp; Dressings", "Rubber, vinyl and plastic brought back and held there."),
 ("scents",           "Scents",             "Odour neutralised at the source, not perfumed over."),
 ("microfiber",       "Microfiber Towels",  "A weight for every surface and every step."),
 ("brushes",          "Brushes &amp; Applicators", "For the places a towel physically cannot reach."),
 ("cannons",          "Cannons &amp; Sprayers", "Foam cannons, pressure guns, sprayers and buckets."),
 ("golf-cart",        "Golf Cart",          "Cart paint, plastic panels and vinyl bench seats."),
 ("marine",           "Marine",             "Gelcoat, vinyl seating and trim that live in sun and salt."),
 ("off-road",         "Off-Road &amp; UTV", "Mud, trail dust and baked-on film."),
]
# product handle -> subcategory
SUB_OF = {
 "luxpro-waterless-wash-detail-spray":"wash-waterless","luxfoam-foam-cannon-soap":"wash-waterless",
 "luxquick-detail-spray":"wash-waterless","ceramicx-ceramic-detail-spray":"ceramic",
 "luxwheelassassin-wheel-cleaner":"wheels-tires","tirevenom-tire-dressing":"wheels-tires",
 "lux-tire-brush":"wheels-tires","lux-wheel-brush":"wheels-tires",
 "interiorx-interior-cleaner":"interior-cleaners","lux-brush-interior-brush":"interior-cleaners",
 "restorx-rvp-plastic-dressing":"trim-dressings",
 "newcarember-air-freshener":"scents","vanillaember-air-freshener":"scents",
 "3-pack-edgeless-lux-edgeless-microfiber-towels":"microfiber","5-pack-microlux-microfiber-towels":"microfiber",
 "luxtowel-drying-towel":"microfiber","2-pack-luxwindow-waffle-window-towel":"microfiber",
 "towel-tantrum-kit-every-surface-every-step-every-finish":"microfiber",
 "luxmit-wash-mit":"brushes","luxbug-bug-and-tar-remover-sponge":"brushes",
 "2-pack-xpad-applicator-pad":"brushes",
 "luxcannon-foam-cannon":"cannons","luxgun-pressure-washer-gun":"cannons",
 "lux-bucket-car-washing-bucket":"cannons","foamx-sprayer-electric-sprayer":"cannons",
 "lux-sprayer-pump-sprayer":"cannons",
 "birdielux-golf-cart-exterior-cleaner":"golf-cart","xfresh-golf-cart-interior-cleaner":"golf-cart",
 "fairway-finish-system":"golf-cart","trail-foam-coming-soon":"off-road",
}
SUB_GROUP = {s: g for g, _, _, subs in GROUPS for s in subs}

DETAIL_EXTRA = {'luxquick-detail-spray': {'features': [('The between-washes reset', 'Pulls light dust, fingerprints, smudges and fresh water spots without touching a hose.'), ('Instant gloss', 'Boosts depth and slickness so the panel looks like it was just finished.'), ('Leaves a slick layer', 'Dust has less to grab, so the car stays cleaner between real washes.'), ('Safe on almost everything outside', 'Paint, clear coat, glass, chrome, plastic trim, PPF, vinyl wrap and ceramic coatings.'), ('15 to 25 vehicles a bottle', 'Small enough to live in the trunk on show day.')], 'caution': ('Light soil only', 'If the panel is properly dirty this is the wrong tool. Foam and rinse first, then reach for LuxQuick.'), 'tips': ['Keep one in the car for shows and post-drive touch-ups.', 'Mist one panel at a time and buff with a dry towel face.', 'Works on fresh water spots &mdash; baked-on mineral needs polishing.', 'Great on glass, where most detail sprays streak.']}, 'restorx-rvp-plastic-dressing': {'features': [('Brings faded trim back', 'Rubber, vinyl and plastic restored to an even, factory-looking finish.'), ('Up to 8 months inside, 6 outside', 'Real UV protection, not a shine that washes off in the first rain.'), ('Never oily', 'Levels into the surface rather than sitting on it, so it does not stay tacky or pull dust.'), ('Works everywhere plastic does', 'Exterior trim, dashboards, door panels, engine bay components, tires and rubber seals.'), ('20 to 40 vehicles a bottle', 'A little goes further than you expect &mdash; porous trim drinks the first coat.')], 'caution': ('Clean and dry first', 'Dressing over dirt seals it in and the trim comes out blotchy. This is the step people skip.'), 'tips': ['Apply with an XPad, not by spraying directly.', 'Let it level for a minute, then wipe back anything that has not absorbed.', 'On badly chalked trim, expect to need a second thin coat.', 'Test somewhere hidden first &mdash; some trim is satin-painted, not plastic.', 'Do the engine bay while you have the pad in your hand. It transforms how it reads.']}, 'newcarember-air-freshener': {'features': [('Neutralises, then scents', 'Kills the odour at the source instead of layering perfume over it.'), ('Clean new-car note', 'Crisp rather than sweet, and it does not turn cloying by day three.'), ('Long-lasting', 'Holds through a week of daily driving.'), ('Safe on carpet and fabric mats', 'Spray the footwells, not the dash.')], 'caution': None, 'tips': ['Air the cabin out before you spray anything.', 'Two or three sprays into the footwells is plenty.', 'One short burst into the vents with the fan running spreads it evenly.', 'Pair with VanillaEmber and alternate &mdash; nose blindness is real.']}, 'vanillaember-air-freshener': {'features': [('Warm vanilla, not candy', 'Smooth and low rather than the sweet hit most vanilla fresheners land on.'), ('Same neutralising base', 'Handles the odour first, then scents.'), ('Long-lasting', 'A week of daily driving from a few sprays.'), ('Safe on carpet and fabric mats', 'Footwells and mats, not hard surfaces.')], 'caution': None, 'tips': ['Air the cabin out first.', 'Two or three sprays into the footwells.', 'One burst into the vents with the fan on.', 'The Dual Scent System pairs it with NewCarEmber if you want to rotate.']}, 'birdielux-golf-cart-exterior-cleaner': {'features': [('Built for cart surfaces', 'Painted panels, moulded plastic bodywork and trim, which behave nothing like automotive clear coat.'), ('Waterless', 'Cleans where the cart sits. Most carts never get near a hose.'), ('Streak-free', 'Cart plastic shows every smear. This does not leave one.'), ('Handles cart-path film', 'Dust, pollen, grass and the grime that comes off a path in the wet.')], 'caution': ('Grit needs rinsing first', 'Same rule as any waterless product. If you can feel it, do not wipe it.'), 'tips': ['One panel at a time, with a clean Edgeless Lux towel.', 'Never dry-wipe an acrylic windshield &mdash; flood it first.', 'Blow or brush loose sand off before anything wet touches the cart.', 'Keep the bottle with the cart, not in a garage across town.']}, 'xfresh-golf-cart-interior-cleaner': {'features': [('Dries clean on vinyl', 'No slick film, which matters a lot on a bench seat with no belts.'), ('Made for cart interiors', 'Seats, dash, trim and the textured vinyl carts are covered in.'), ('Handles a season outdoors', 'Sunscreen, sweat, grass and rain, which is what cart seats actually take.'), ('No greasy residue', 'Nothing transfers onto clothes.')], 'caution': None, 'tips': ['Spray onto the towel, not the seat.', 'Work one section and follow with a dry towel face.', 'A LuxBrush gets into textured vinyl a towel skates over.', 'Do the seats before the bodywork so overspray lands on unwashed panels.']}, 'trail-foam-coming-soon': {'features': [('Built for mud, not dust', 'A foam that clings long enough to soften dried trail film before anything touches the paint.'), ('In development', 'Being tested against real trail vehicles before it ships.')], 'caution': ('Not available yet', 'Trail Foam is still in development. Everything else in Off-Road is shipping today.'), 'tips': []}, '3-pack-edgeless-lux-edgeless-microfiber-towels': {'features': [('No stitched edge', 'A sewn border is a hard seam being dragged across your clear coat. These have none.'), ('Exterior weight', 'High pile, so grit lifts up into the nap instead of staying pinned against the paint.'), ('What the formulas were built around', 'Every waterless and ceramic instruction on this site says to use these.'), ('Three to a pack', 'A full vehicle takes four to six towel faces. Fold in quarters and you get eight per towel.')], 'caution': None, 'tips': ['Keep exterior and interior towels in separate piles.', 'Wash warm, no fabric softener &mdash; it coats the fibres and kills absorbency.', 'The moment one touches the ground it becomes a wheel towel for life.', 'If a towel comes out slick rather than grabby, it is contaminated.']}, '5-pack-microlux-microfiber-towels': {'features': [('Interior weight', 'Lighter pile that does not push cleaner around on a hard panel.'), ('Five to a pack', 'An interior burns through towels &mdash; cleaner, dry, glass, jambs.'), ('Lint-free on dark plastic', 'Where most towels leave a visible haze.'), ('Safe on screens', 'Fine enough for navigation glass when barely damp.')], 'caution': None, 'tips': ['Spray product onto the towel, never onto the panel.', 'Keep one dedicated to glass and nothing else.', 'Wash separately from exterior towels.', 'No fabric softener, ever.']}, 'luxtowel-drying-towel': {'features': [('1300 GSM, 2 ft × 3 ft', 'Enough capacity to take a full vehicle down in one pass.'), ('Ultra-plush pile', 'Glides rather than drags, which is what prevents drying-stage swirls.'), ('Reduces water spotting', 'Getting the water off fast is the whole game in hard-water regions.'), ('Big enough to lay flat', 'Drape and drag rather than scrub.')], 'caution': ('Drying towel, not a wash towel', 'The deep pile traps grit where you cannot see it. Do not use it for waterless work.'), 'tips': ['Lay it flat and drag, or blot. Never scrub.', 'Get into panel gaps and mirror housings or water runs out later.', 'Wring it out mid-car rather than pushing through.', 'Wash it on its own &mdash; it holds more than you think.']}, '2-pack-luxwindow-waffle-window-towel': {'features': [('Waffle weave', 'The only structure that leaves the inside of a windshield without haze.'), ('Two to a pack', 'One damp, one dry &mdash; the two-towel glass method.'), ('Lint-free', 'No fibres left in the corners.'), ('Works on cart and boat acrylic', 'Where a standard towel marks the surface.')], 'caution': None, 'tips': ['Damp towel first, dry towel second. Always two.', 'Wipe the inside horizontally and the outside vertically &mdash; then you know which side a streak is on.', 'Never use ammonia glass cleaner on acrylic; it crazes it.', 'Keep these away from wax and dressing residue.']}, 'luxmit-wash-mit': {'features': [('Deep pile', 'Carries a lot of lubricant, which is what keeps the mitt gliding.'), ('Traps grit away from paint', 'Dirt lifts up into the nap instead of sitting under your hand.'), ('Fits the two-bucket method', 'Rinse it out between panels and the grit leaves the mitt.'), ('Covers a full vehicle', 'One mitt, top-down, rinsing often.')], 'caution': None, 'tips': ['Two buckets. The rinse bucket is the one doing the safety work.', 'Top panels first, rockers and bumpers last.', 'Drop it once and it is a wheel-well mitt from then on.', 'Rinse and hang to dry rather than balling it up wet.']}, 'luxbug-bug-and-tar-remover-sponge': {'features': [('For the front end', 'Bumper, mirror caps and the leading edge of the hood, where bugs bake on.'), ('Safe on clear coat', 'Lifts bug residue without the scouring that ruins a bumper.'), ('Works wet, with soap', 'Use it during the wash, not dry.'), ('Rinses out clean', 'Does not hold residue between uses.')], 'caution': ('Always use it wet and lubricated', 'Dry, this will mar the finish. Soap and water first, every time.'), 'tips': ['Soak the front end and let the bugs soften before you touch them.', 'Light pressure. Let the sponge structure do the work.', 'Rinse it out constantly while you work.', 'Follow with LuxQuick or CeramicX &mdash; bug acid strips protection.']}, '2-pack-xpad-applicator-pad': {'features': [('Even dressing application', 'Spraying TireVenom or RestorX directly puts it on your paint and in the lettering. A pad does not.'), ('Contoured for sidewalls', 'Holds a line around the curve of a tire.'), ('Washable and reusable', 'Rinse out and they come back.'), ('Two to a pack', 'One for tires, one for trim. Never share them.')], 'caution': None, 'tips': ['Keep tire and trim pads separate &mdash; tire dressing contaminates a trim pad.', 'Load lightly. More product means sling, not shine.', 'Level the surface with the pad after applying.', 'Rinse them out before the dressing sets.']}, 'luxcannon-foam-cannon': {'features': [('Where the dwell time comes from', 'Without a cannon, foam soap is just soap. The clinging blanket is the whole point.'), ('Adjustable mix and fan', 'Dial thickness from the cannon before you add more soap to the bottle.'), ('Standard pressure-washer fitting', 'Swaps with the LuxGun in one click.'), ('Wide fan for full coverage', 'Blankets a vehicle bottom to top in under a minute.')], 'caution': ('Needs a pressure washer', "This is not a hose attachment. Output depends on your unit's flow rate."), 'tips': ['Rinse the vehicle before you foam. Never foam a dry, dusty panel.', 'Foam bottom to top, rinse top to bottom.', 'Adjust the dial before adding concentrate &mdash; it is cheaper.', 'Hard water suppresses foam. If yours is thin, that is usually why.']}, 'luxgun-pressure-washer-gun': {'features': [('Short body', 'You are not fighting a two-foot wand around a wheel arch.'), ('Full quick-connect nozzle set', '0°, 15°, 25°, 40° and soap, so one gun covers every job.'), ('One-click swap to the cannon', 'Foam and rinse without changing setup.'), ('Built to last', 'Metal fittings rather than moulded plastic.')], 'caution': ('Never use the 0° nozzle on paint', 'It is for concrete and wheel wells. On a panel it will damage the finish.'), 'tips': ['40° for rinsing paint, 25° for wheel wells, 15° for stubborn ground-in dirt.', 'Keep a foot of distance from any panel.', 'Rinse top to bottom, always.', 'Drain it after use if it lives somewhere that freezes.']}, 'lux-bucket-car-washing-bucket': {'features': [('Half of a two-bucket wash', 'One soap, one rinse. The oldest swirl-prevention method there is, and still the best.'), ('Grit-guard sized', 'Takes a standard guard so dirt stays on the bottom.'), ('Holds a full wash', 'Enough volume that the soap does not go grey halfway round.'), ('Stackable', 'Two of these store as one.')], 'caution': None, 'tips': ['Buy two. One bucket is not the two-bucket method.', 'Rinse the mitt in the rinse bucket between every panel.', 'Dump and refill if the rinse water goes properly dirty.', 'Keep a separate bucket for wheels and never cross them over.']}, 'foamx-sprayer-electric-sprayer': {'features': [('No pumping', 'Even, continuous output for the whole job.'), ('Consistent coverage', 'Matters most on waterless and dressing work, where uneven product means streaks.'), ('Rechargeable', 'Enough runtime for several vehicles.'), ('Adjustable output', 'Mist for waterless, heavier for pre-soak.')], 'caution': None, 'tips': ['Great for pre-soaking wheels and arches before you touch them.', 'Rinse it through with clean water after any dressing.', 'Dial the output down for waterless &mdash; you want a mist, not a stream.', 'Charge it the night before a full detail.']}, 'lux-sprayer-pump-sprayer': {'features': [('No power needed', 'Pumps up and holds pressure for the whole panel.'), ('For pre-soak and dilution', 'Where you want volume rather than a fine mist.'), ('Chemical resistant', 'Handles diluted wheel cleaner and soap.'), ('Simple to service', 'Nothing to charge, nothing to break.')], 'caution': None, 'tips': ['Label it. A sprayer that has held wheel cleaner should not later hold detail spray.', 'Rinse through after every use.', 'Release the pressure before storing it.', 'Pairs well with LuxFoam for a bucket-free pre-soak.']}, 'lux-tire-brush': {'features': [('Stiff bristles', 'Soft brushes do not shift antiozonant bloom, and bloom is what makes tires go brown.'), ('Sized for sidewalls', 'Covers the face of a tire in a few passes.'), ('Handles heavy buildup', 'Old dressing, road film and brake dust off the rubber.'), ('Rinses clean', 'Does not hold product between wheels.')], 'caution': ('Tires only', 'This is too stiff for a wheel face. Use the Lux Wheel Brush there.'), 'tips': ['Scrub until the suds run clear, not until it looks better.', 'On a neglected tire, expect two or three passes.', 'Rinse and let the tire dry fully before dressing.', 'This step is the difference between a detail that holds and one that browns.']}, 'lux-wheel-brush': {'features': [('Soft barrel brush', 'Reaches behind the spokes, which is where most of the brake dust actually lives.'), ('Will not mark the finish', 'Safe on clear-coated, painted and polished wheels.'), ('Long enough for deep barrels', 'Gets to the back of a modern concave wheel.'), ('Flexible shaft', 'Follows the curve instead of fighting it.')], 'caution': None, 'tips': ['Let LuxWheelAssassin dwell first. The brush is for agitation, not scrubbing.', 'Do the barrel before the face.', 'Keep it away from tires &mdash; use the tire brush for those.', 'Rinse it out before the cleaner dries in the bristles.']}, 'lux-brush-interior-brush': {'features': [('Curved head', 'Follows vents, seams and the shape of a dash.'), ('Soft enough for piano black', 'Where a stiff brush leaves visible marks.'), ('Gets into switchgear', 'Around buttons, stalks and the base of the shifter.'), ('Pairs with InteriorX', 'Agitates textured vinyl a towel just skates over.')], 'caution': None, 'tips': ['Spray the product onto the brush, not into the vent.', 'Light pressure on gloss trim.', 'Follow immediately with a MicroLux towel before it dries.', 'Great on textured door cards where most of the grime hides.']}, 'lux-t': {'features': [('Soft cotton', 'The one you actually end up wearing in the driveway.'), ('Printed mark', 'LusterLux on the chest, nothing shouting.')], 'caution': None, 'tips': []}, 'the-luxcap-limited-supply': {'features': [('Leather patch', 'Structured front, LusterLux patch.'), ('Limited run', 'When this batch is gone it is gone.')], 'caution': None, 'tips': []}}

DETAIL = {'luxpro-waterless-wash-detail-spray': {'features': [('NanoFusion encapsulation', 'Nano-polymers wrap each particle of dust and road film so it lifts clear of the paint instead of being dragged across it.'), ('High-lubricity carrier', 'The towel rides on liquid, not on your clear coat. This is what separates a maintenance wipe from a panel full of swirls.'), ('Leaves protection behind', 'An ultra-thin hydrophobic layer that adds gloss, tightens water beading and slows how fast dust bonds back on.'), ('No hose, no bucket, no runoff', 'Works in an apartment car park, a garage, or on a show field.'), ('Safe across the whole exterior', 'Paint, clear coat, glass, chrome, plastic trim, wheels, PPF, vinyl wrap and existing ceramic coatings.'), ('15 to 30 vehicles a bottle', 'One 16 oz bottle covers most daily drivers for the better part of a year.')], 'caution': ('Not for a genuinely dirty car', 'Waterless is for light dust, pollen, fingerprints and road film. If you can feel grit on the panel, rinse or foam it off first.'), 'tips': ['Work one panel at a time, out of direct sun.', 'Spray more than feels reasonable. Under-spraying is what causes scratches.', 'Straight-line wipes, front to back. Never circles.', 'Rotate to a fresh towel face every panel or two.', 'Use Edgeless Lux towels &mdash; the formula was built around them.']}, 'ceramicx-ceramic-detail-spray': {'features': [('Bonds in minutes', 'A durable ceramic layer laid down in the time it takes to wipe a panel.'), ('Up to 8 months', 'With proper application and maintenance, one application holds through a season and then some.'), ('Extreme hydrophobics', 'Water beads tight and sheets off fast, which is what stops mineral spotting from setting in.'), ('Layers over what you already have', 'Tops up an existing coating rather than replacing it.'), ('Real gloss depth', 'Enhances colour depth rather than just adding surface shine.'), ('10 to 20 vehicles a bottle', 'Two to three sprays a panel is all it takes.')], 'caution': ('Needs a clean, cool, dry surface', 'Sealing dirt under a coating locks it in. Wash or waterless first, always.'), 'tips': ['Two to three sprays per panel, no more.', 'Spread with one towel, buff off with a second dry one.', 'Give it an hour before it sees rain.', 'Use it after LuxPro or a foam wash, never instead of one.']}, 'luxfoam-foam-cannon-soap': {'features': [('Thick, clinging foam', 'Stays on the panel long enough to break down road film instead of sliding straight off.'), ('High lubricity', 'The mitt glides rather than grabs &mdash; the single biggest thing standing between a wash and a swirl.'), ('Encapsulating', 'Dirt stays suspended in the suds where it cannot cut into the clear coat.'), ('Coating and wax safe', 'Rinses clean with no residue and will not strip what is already on the car.'), ('Cannon or two-bucket', 'Works either way, though the cannon is where the dwell time comes from.'), ('8 to 16 washes a bottle', 'Highly concentrated, so start leaner than you think.')], 'caution': ('Never foam a dry, dusty panel', 'Rinse the loose grit off with water first, or you are just gluing it in place.'), 'tips': ['Foam bottom to top so the dirtiest panels never sit uncovered.', 'Let it dwell two to five minutes, in shade.', 'Rinse top to bottom before it dries.', 'Dial thickness from the cannon before you add more soap.', 'Watch the runoff &mdash; brown means it is working.']}, 'luxwheelassassin-wheel-cleaner': {'features': [('Breaks brake dust down chemically', 'Releases bonded metal so you are not scrubbing a finish you cannot replace.'), ('Minimal agitation', 'Most of the work happens while it dwells, not while you scrub.'), ('Safe across wheel finishes', 'Clear-coated, painted, chrome, alloy and factory wheels.'), ('Cuts grease and road film', 'Not just the surface dust that rinses off anyway.'), ('12 to 20 vehicles a bottle', 'Enough for a season of weekly washes.')], 'caution': ('Test an inconspicuous area first', 'And never let it dry on the wheel. Work cool wheels, out of direct sun.'), 'tips': ['Spray the barrel, not just the face. That is where the dust lives.', 'Agitate with a wheel brush where buildup is heavy.', 'Wheels come first in a wash, before any paint.', 'Rinse thoroughly and dry before you dress the tires.']}, 'tirevenom-tire-dressing': {'features': [('No-sling, dries to the touch', 'Stays on the sidewall instead of striping down your rocker panel on the first pull-out.'), ('Deep, even black', 'Restores faded rubber without the wet-look gloss that reads cheap.'), ('UV, cracking and browning defence', 'Up to three months from a single application.'), ('Never greasy', 'It does not stay tacky, so it does not collect dust the moment you park.'), ('30 to 50 tires a bottle', 'A 16 oz bottle lasts most people a year.')], 'caution': ('Scrub the sidewall clean first', 'Dressing over old dressing is exactly what causes browning. This step is not optional.'), 'tips': ['Apply with an XPad rather than spraying directly.', 'Level out any heavy spots before it sets.', 'Let it set before you drive.', 'Dress tires last, after the car is washed and dry.']}, 'interiorx-interior-cleaner': {'features': [('Dries to a factory matte', 'No gloss, so nothing reflects back at you off the dash in low sun.'), ('No greasy residue', 'A steering wheel stays a steering wheel.'), ('Lifts real interior soil', 'Fingerprints, spills, dust and everyday grime, not just surface dust.'), ('Safe across the cabin', 'Dashboards, door panels, consoles, steering wheels, vinyl, plastic and rubber.'), ('15 to 25 vehicles a bottle', 'Enough for routine upkeep and the occasional deep clean.')], 'caution': None, 'tips': ['Spray onto the towel, not the panel.', 'Work one section at a time and follow with a dry towel face.', 'Use a LuxBrush for vents, seams and switchgear.', 'Do the interior before the exterior so overspray lands on unwashed paint.']}}

DETAIL.update(DETAIL_EXTRA)
KITS = {'waterless-wash-system-1': {'includes': ['1× LuxPro Waterless Wash, 16 oz', '3× Edgeless Lux Exterior Microfiber Towels'], 'features': [('The entry point into NanoFusion', 'The bottle and the towels it was formulated to be used with, nothing else to buy.'), ('No hose, bucket or running water', 'Works in an apartment car park, a garage, or on a show field.'), ('Cleans, glosses and protects in one pass', 'One step instead of wash, dry, then protect.'), ('Cheapest way to find out if it works', 'If NanoFusion does not do what we say, you are out the price of a bottle.')], 'who': 'Anyone curious about waterless washing, or living somewhere a hose is not an option.'}, 'complete-detail-system-1': {'includes': ['1× LuxPro Waterless Wash', '1× RestorX RVP Dressing', '1× InteriorX Interior Cleaner', '3× Edgeless Lux Exterior Towels', '5× MicroLux Interior Towels', '1× XPad Applicator'], 'features': [('Exterior and interior in one box', 'Paint, trim and cabin covered without picking nine bottles yourself.'), ('The three chemicals that do the most', 'Waterless wash, trim restorer and interior cleaner cover the majority of a detail.'), ('Both towel weights included', 'Exterior and interior, kept separate as they should be.'), ('Applicator for the dressing', 'So RestorX goes on evenly instead of in streaks.')], 'who': 'The default starting point. If you are buying one thing, buy this.'}, 'paint-care-system-1': {'includes': ['1× LuxPro Waterless Wash', '1× LuxQuick Detail Spray', '1× CeramicX Ceramic Spray', '3× Edgeless Lux Exterior Towels'], 'features': [('Paint only, done properly', 'Clean, maintain and protect, in the order you actually use them.'), ('Covers the full maintenance cycle', 'LuxPro for the wash, LuxQuick between washes, CeramicX for protection.'), ('Up to 8 months of ceramic protection', 'From the CeramicX in the box.'), ('Edgeless towels throughout', 'No stitched seam dragged across your clear coat.')], 'who': 'Someone who cares about the paint and lets a detailer handle the rest.'}, 'tire-care-system-1': {'includes': ['1× TireVenom Tire Dressing', '2× XPad Applicator Pads'], 'features': [('Dressing and the pads to apply it', 'Spraying dressing directly is what puts it on your paint.'), ('No-sling, dries to the touch', 'Stays on the sidewall through the first pull-out.'), ('Up to 3 months an application', '30 to 50 tires from the bottle.'), ('Reusable pads', 'Rinse them out and they come back.')], 'who': 'Cheapest upgrade to how a clean car looks. Tires are the first thing people notice.'}, 'rim-and-tire-system-kit-1': {'includes': ['1× LuxWheelAssassin Wheel Cleaner', '1× TireVenom Tire Dressing', '1× Lux Wheel Brush', '1× Lux Tire Brush', '2× XPad Applicator Pads'], 'features': [('Wheels and tires as one job', 'Because they are. Clean the wheel, scrub the sidewall, dress it last.'), ('Both brushes, and they are different', 'A soft barrel brush for wheel faces, a stiff one for sidewalls. Using the wrong one is how wheels get marked.'), ('Chemical brake-dust removal', 'So you are not scrubbing a finish you cannot replace.'), ('Everything in the right order', 'Nothing missing from the corner of the car people look at first.')], 'who': 'Anyone whose wheels are the worst-looking part of an otherwise clean vehicle.'}, 'foam-wash-system-1': {'includes': ['1× LuxCannon Foam Cannon', '2× LuxFoam Foam Soap, 16 oz'], 'features': [('A proper foam wash from nothing', 'Cannon plus two bottles of soap. Add a pressure washer and you are set.'), ('Dwell time is the safety', 'Every minute foam sits on the panel is cleaning happening with nothing touching the paint.'), ('Adjustable cannon', 'Dial thickness from the cannon rather than burning through concentrate.'), ('Two bottles', '8 to 16 washes each, so this lasts a season or more.')], 'who': 'Anyone who owns a pressure washer and is still washing with a bucket and a sponge.'}, 'ultimate-wash-system-1': {'includes': ['1× LuxGun Pressure Washer Gun', '1× LuxCannon Foam Cannon', '1× LuxFoam Foam Soap', '1× LuxTowel Drying Towel', '1× Quick-Connect Coupler'], 'features': [('The whole wash bay', 'Gun, cannon, soap and drying towel. Foam through dry, nothing else needed.'), ('Quick-connect throughout', 'Swap between gun and cannon in one click, no tools.'), ('Full nozzle set', '0°, 15°, 25°, 40° and soap, so one gun covers every job.'), ('1300 GSM drying towel', 'Takes a full vehicle down in one pass, which is what prevents water spotting.')], 'who': 'Someone building a wash setup from scratch, or replacing a hardware-store one.'}, 'complete-interior-system-1': {'includes': ['1× InteriorX Interior Cleaner', '1× Lux Brush Curved Detailing Brush', '1× Lux Brush Holder', '5× MicroLux Interior Towels', '1× NewCarEmber Air Freshener', '1× VanillaEmber Air Freshener'], 'features': [('A full cabin reset', 'Cleaner, brush, towels and both scents. Everything the inside of a car needs.'), ('Dries to a factory matte', 'No gloss, so nothing reflects back off the dash.'), ('Brush for the places a towel cannot reach', 'Vents, seams, switchgear and textured door cards.'), ('Five interior towels', 'Because an interior burns through them faster than you expect.')], 'who': 'Daily drivers, family cars, and anything that has been lived in.'}, 'interior-restoration-system-1': {'includes': ['1× InteriorX Interior Cleaner', '1× RestorX RVP Dressing', '5× MicroLux Interior Towels'], 'features': [('For a cabin that has been let go', 'Clean first, then bring the faded plastics back and hold them there.'), ('Up to 8 months of interior protection', 'From the RestorX, which is what stops it fading again.'), ('Clean then restore, in that order', 'Dressing over dirt seals it in and comes out blotchy.'), ('No greasy residue from either', 'Nothing tacky, nothing pulling dust.')], 'who': 'Older vehicles, sun-baked dashes, and anything with grey chalky trim.'}, 'dual-scent-system-1': {'includes': ['1× NewCarEmber Air Freshener', '1× VanillaEmber Air Freshener'], 'features': [('Both Ember scents', 'Clean new-car and warm vanilla.'), ('Neutralises rather than masks', 'Handles the odour at the source first.'), ('Rotate them', 'Nose blindness is real. Alternating keeps either one noticeable.'), ('Safe on carpet and fabric mats', 'Spray the footwells, not the dash.')], 'who': "Anyone whose cabin smells like the dog, the gym bag or last week's drive-through."}, 'the-platinum-system': {'includes': ['4× LuxFoam Foam Soap', '3× LuxPro Waterless Wash', '2× LuxQuick Detail Spray', '3× LuxWheelAssassin Wheel Cleaner', '1× TireVenom Tire Dressing', '3× InteriorX Interior Cleaner', '1× RestorX RVP Dressing', '1× LuxCannon Foam Cannon', '1× Lux Bucket', '1× LuxMitt Wash Mitt', '1× LuxTowel Drying Towel', '1× LuxWheel Brush', '1× Lux Tire Brush', '1× Lux Brush', '1× LuxBug Bug &amp; Tar Sponge', '2× 3-Pack Edgeless Lux Towels', '5-Pack MicroLux Towels', '2× 2-Pack XPad Applicators', '1× NewCarEmber', '1× VanillaEmber'], 'features': [('Over $700 of product for $500', 'Every chemical, every tool, every towel weight LusterLux makes.'), ('Multiples of the things you run out of', 'Four foam soaps, three waterless, three wheel cleaners, three interior cleaners.'), ('Nothing left to buy', 'Foam through dry, wheels through interior, scent at the end.'), ('Built for volume', 'Enough product to run a season of weekly details, or a small shop.')], 'who': 'The person whose garage is the hobby, and shops that are tired of reordering piecemeal.'}, 'fairway-finish-system': {'includes': ['1× BirdieLux Golf Cart Exterior Cleaner', '1× XFresh Cart Interior Cleaner', '5× MicroLux Interior Towels', '3× Edgeless Lux Exterior Towels', '1× Lux Detail Brush'], 'features': [('Every surface on a cart', 'Painted panels, plastic bodywork, vinyl seats, dash and trim.'), ('Waterless throughout', 'Carts rarely live near a hose. This works where the cart is parked.'), ('Both towel weights', 'Exterior for panels, interior for seats and dash.'), ('Brush for textured vinyl', 'Where a towel just skates across the top.')], 'who': 'Anyone with a cart worth as much as a used car, cleaned like garden furniture.'}, 'towel-tantrum-kit-every-surface-every-step-every-finish': {'includes': ['1× LuxTowel Drying Towel', '3× Edgeless Lux Exterior Towels', '5× MicroLux Interior Towels', '2× LuxWindow Waffle Weave Window Towels'], 'features': [('A weight for every step', 'Drying, exterior, interior and glass are four different jobs and four different weaves.'), ('Eleven towels', 'Enough to do a full vehicle without reusing a dirty face.'), ('Keeps the piles separate', 'Which is the actual point &mdash; an interior towel on paint is how swirls start.'), ('Waffle weave for glass', 'The only structure that leaves an inside windshield without haze.')], 'who': 'Anyone still doing a whole car with two towels and hoping.'}}
DETAIL.update(KITS)


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
            "features": (DETAIL.get(h) or {}).get("features", []),
            "caution": (DETAIL.get(h) or {}).get("caution") or [],
            "tips": (DETAIL.get(h) or {}).get("tips", []),
            "includes": (DETAIL.get(h) or {}).get("includes", []),
            "who": (DETAIL.get(h) or {}).get("who", ""),
            "soon": price == 0,
            "storeUrl": f"{STORE}/products/{h}",
            "url": f"/products/{h}/",
        }
        checks = [(f, item[f]) for f in ("line", "short", "desc", "showBody", "showWhy", "who")]
        checks += [(f"includes[{i}]", x) for i, x in enumerate(item["includes"])]
        checks += [(f"tips[{i}]", x) for i, x in enumerate(item["tips"])]
        checks += [(f"features[{i}]", " ".join(x)) for i, x in enumerate(item["features"])]
        if item["caution"]: checks.append(("caution", " ".join(item["caution"])))
        for field, val in checks:
            m = BANNED.search(val or "")
            if m: problems.append(f"banned word in {h}.{field}: {m.group(0)}")
        items.append(item)

    # validate pair references resolve
    handles = {i["h"] for i in items}
    for i in items:
        for pr in i["pairs"]:
            if pr not in handles:
                problems.append(f"{i['h']} pairs with missing handle {pr}")

    items.sort(key=lambda i: (i["hero"] == 0, i["hero"], i["cat"], -i["price"]))
    for i in items:
        sub = SUB_OF.get(i["h"], "")
        if not sub and i["cat"] == "kits-systems": sub = ""
        i["sub"] = sub
        i["group"] = SUB_GROUP.get(sub, "kits-systems" if i["cat"] == "kits-systems"
                                   else ("beyond-the-car" if i["cat"] == "beyond-the-car" else ""))
        if i["cat"] == "merch": i["group"] = "merch"
        w = []
        if i["h"] not in NOT_CAR and i["cat"] != "merch":
            w.append("car-truck")
        for wk, members in WORLD_MEMBERS.items():
            if i["h"] in members:
                w.append(wk)
        i["worlds"] = w
    cats = [{"k": k, "t": t, "d": d} for k, t, d in CATS] + [{"k": MERCH[0], "t": MERCH[1], "d": MERCH[2]}]
    worlds = [{"k": k, "t": t, "d": d, "img": im} for k, t, d, im in WORLDS]
    groups = [{"k": k, "t": t, "d": d, "subs": subs} for k, t, d, subs in GROUPS]
    subs = [{"k": k, "t": t, "d": d, "g": SUB_GROUP.get(k, "")} for k, t, d in SUBS]
    payload = {"cats": cats, "groups": groups, "subs": subs, "worlds": worlds, "products": items,
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
    print("  --- groups ---")
    for g in groups:
        n = sum(1 for i in items if i["group"] == g["k"])
        print(f"  {g['k']:<16} {n}")
        for sk in g["subs"]:
            print(f"     {sk:<20} {sum(1 for i in items if i['sub']==sk)}")
    unassigned=[i["h"] for i in items if not i["group"]]
    if unassigned: print("  UNGROUPED:", unassigned)
    print("  --- worlds ---")
    for w in worlds:
        print(f"  {w['k']:<16} {sum(1 for i in items if w['k'] in i['worlds'])}")
    print("\nPROBLEMS:", *(problems or ["none"]), sep="\n  ")


if __name__ == "__main__":
    main()
