#!/usr/bin/env python3
"""Generate the deployable index.html from the Claude Design source.

Keeps 'Balaji Enterprises.dc.html' untouched as the editable design source; the
live page differs from it in exactly three ways:
  1. a real <head> (title / description / favicon / lang)
  2. the image-slot authoring widget swapped for a neutral placeholder
  3. no dependency on image-slot.js
"""
import sys, pathlib, re, hashlib

src = pathlib.Path(sys.argv[1]).read_text()
out = pathlib.Path(sys.argv[2])

def sub(old, new, label):
    global src
    if old not in src:
        sys.exit("FAILED to find anchor: " + label)
    src = src.replace(old, new, 1)

# --- 1. head -------------------------------------------------------------
SITE  = "https://www.rbalajient.com/"
TITLE = "Balaji Enterprises: Industrial Tools &amp; MRO Supplier, Indore"  # 60 chars
DESC  = ("Authorised distributor of hand tools, power tools, measuring instruments "
         "and industrial MRO equipment in Indore. 12,000+ items, 25 brands, since "
         "1996.")  # 150 chars

JSONLD = """{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": ["LocalBusiness", "HardwareStore"],
      "@id": "https://www.rbalajient.com/#business",
      "name": "Balaji Enterprises",
      "description": "Authorised distributor of hand tools, power tools, measuring instruments and industrial MRO equipment serving manufacturers, dealers and businesses across Madhya Pradesh.",
      "url": "https://www.rbalajient.com/",
      "logo": "https://www.rbalajient.com/assets/logo.png",
      "image": "https://www.rbalajient.com/assets/logo.png",
      "foundingDate": "1996",
      "priceRange": "$$",
      "currenciesAccepted": "INR",
      "alternateName": "\u092c\u093e\u0932\u093e\u091c\u0940 \u090f\u0902\u091f\u0930\u092a\u094d\u0930\u093e\u0907\u091c\u0947\u091c",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "118, Siyaganj Main Road, Siyaganj",
        "addressLocality": "Indore",
        "addressRegion": "Madhya Pradesh",
        "postalCode": "452007",
        "addressCountry": "IN"
      },
      "telephone": "+91-9302110344",
      "email": "sales@rbalajient.com",
      "contactPoint": [
        {"@type": "ContactPoint", "telephone": "+91-9302110344", "contactType": "sales", "email": "sales@rbalajient.com", "areaServed": "IN", "availableLanguage": ["en", "hi"]},
        {"@type": "ContactPoint", "telephone": "+91-9691020344", "contactType": "sales", "areaServed": "IN", "availableLanguage": ["en", "hi"]},
        {"@type": "ContactPoint", "telephone": "+91-7805933336", "contactType": "customer support", "areaServed": "IN", "availableLanguage": ["en", "hi"]},
        {"@type": "ContactPoint", "telephone": "+91-7805933337", "contactType": "customer support", "areaServed": "IN", "availableLanguage": ["en", "hi"]},
        {"@type": "ContactPoint", "email": "accounts@rbalajient.com", "contactType": "billing support", "areaServed": "IN"}
      ],
      "geo": {
        "@type": "GeoCoordinates",
        "latitude": 22.7168011,
        "longitude": 75.8644892
      },
      "hasMap": "https://maps.google.com/?cid=14834392374782579213",
      "openingHoursSpecification": [
        {
          "@type": "OpeningHoursSpecification",
          "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
          "opens": "10:00",
          "closes": "19:30"
        },
        {
          "@type": "OpeningHoursSpecification",
          "dayOfWeek": "Sunday",
          "opens": "00:00",
          "closes": "00:00"
        }
      ],
      "sameAs": [
        "https://www.linkedin.com/company/rbalajient/",
        "https://maps.google.com/?cid=14834392374782579213"
      ],
      "areaServed": [
        {"@type": "State", "name": "Madhya Pradesh"},
        {"@type": "City", "name": "Indore"}
      ],
      "knowsAbout": ["Hand Tools", "Power Tools", "Cutting Tools & Abrasives", "Measuring & Layout", "Lubrication & Fluid Handling", "Tool Storage & Workshop", "Lifting & Pulling", "Material Handling", "Industrial MRO Supply"],
      "hasOfferCatalog": {
        "@type": "OfferCatalog",
        "name": "Balaji Enterprises Product Catalogue",
        "itemListElement": [
          {"@type": "OfferCatalog", "name": "Hand Tools"},
          {"@type": "OfferCatalog", "name": "Power Tools"},
          {"@type": "OfferCatalog", "name": "Cutting Tools & Abrasives"},
          {"@type": "OfferCatalog", "name": "Measuring & Layout"},
          {"@type": "OfferCatalog", "name": "Lubrication & Fluid Handling"},
          {"@type": "OfferCatalog", "name": "Tool Storage & Workshop"},
          {"@type": "OfferCatalog", "name": "Lifting & Pulling"},
          {"@type": "OfferCatalog", "name": "Material Handling"}
        ]
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://www.rbalajient.com/#website",
      "url": "https://www.rbalajient.com/",
      "name": "Balaji Enterprises",
      "publisher": {"@id": "https://www.rbalajient.com/#business"},
      "inLanguage": "en-IN"
    }
  ]
}"""

sub(
'''<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="./support.js" defer></script>
</head>''',
f'''<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="{SITE}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#081B33">
<link rel="icon" href="assets/logo.png" type="image/png">
<link rel="apple-touch-icon" href="assets/logo.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Balaji Enterprises">
<meta property="og:locale" content="en_IN">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="{SITE}assets/logo.png">
<meta property="og:url" content="{SITE}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="{SITE}assets/logo.png">
<script type="application/ld+json">{JSONLD}</script>
<script src="./support.js" defer></script>
</head>''', "head block")

# --- 2. drop the image-slot authoring import -----------------------------
sub(
'''<div style="position:absolute;width:0;height:0;overflow:hidden;opacity:0;pointer-events:none">
  <x-import component-from-global-scope="image-slot" from="./image-slot.js" hint-size="1,1"></x-import>
</div>

''', "", "image-slot import")

# --- 3. authoring drop-target -> neutral placeholder ---------------------
sub(
'''                  <image-slot id="slot-{{ prod.slotId }}" shape="rect" fit="contain" placeholder="{{ prod.slotHint }}"></image-slot>
                  <sc-if value="{{ prod.hasPhoto }}">
                    <div role="img" aria-label="{{ prod.name }}" style="{{ prod.photoStyle }}"></div>
                  </sc-if>''',
'''                  <sc-if value="{{ prod.hasPhoto }}">
                    <div role="img" aria-label="{{ prod.name }}" style="{{ prod.photoStyle }}"></div>
                  </sc-if>
                  <sc-if value="{{ prod.noPhoto }}">
                    <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;padding:14px;text-align:center;background:#FBF8F2">
                      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#CBC1AE" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><path d="M21 15l-5-5L5 21"></path></svg>
                      <span style="font-size:11px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;color:#A99F8D">Photo on request</span>
                    </div>
                  </sc-if>''', "product image slot")

# --- 4. expose the inverse flag -----------------------------------------
sub("        hasPhoto: !!photoUrl,",
    "        hasPhoto: !!photoUrl,\n        noPhoto: !photoUrl,", "hasPhoto flag")

# --- 5. strip the now-dead authoring props (nothing reads them once the
#        image-slot element is gone; they'd otherwise ship a stray
#        "Drop a <product> photo" string in the page source) ------------------
before = src
src = re.sub(r'\n\s*slot(?:Id|Hint): [^\n]*,(?=\n)', '', src)
removed = len(re.findall(r'slot(?:Id|Hint):', before)) - len(re.findall(r'slot(?:Id|Hint):', src))
if removed != 4:
    sys.exit("expected to strip 4 slot props, stripped %d" % removed)

# --- 6. crawlable catalogue links -----------------------------------------
# The app reaches the catalogue through onClick state changes, so the static
# pages under /products/ would be orphans: reachable from the sitemap but with
# no link equity and nothing for a crawler to follow. A real <a> column in the
# footer gives them a path in, and gives visitors a plain link too.
import json as _json, re as _re
_raw = (out.parent / "catalogue.js").read_text()
_cats = _json.loads(_raw[_raw.index("{"):].rstrip().rstrip(";"))["cats"]
_links = "".join(
    f'<a href="/products/{c["slug"]}/" style="color:rgba(255,255,255,0.6);'
    f'text-decoration:none;font-size:14px" style-hover="color:#fff">'
    f'{c["name"]}</a>' for c in _cats)

sub("padding:56px 32px 32px;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px",
    "padding:56px 32px 32px;display:grid;grid-template-columns:1.3fr 0.8fr 1fr 1fr;gap:36px",
    "footer grid")

sub('''      <div>
        <div style="font-weight:800;font-size:13px;color:#F5883E;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:16px">Contact</div>''',
    f'''      <div>
        <div style="font-weight:800;font-size:13px;color:#F5883E;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:16px">Catalogue</div>
        <div style="display:flex;flex-direction:column;gap:11px">
          <a href="/products/" style="color:rgba(255,255,255,0.6);text-decoration:none;font-size:14px;font-weight:700" style-hover="color:#fff">All products</a>
          {_links}
        </div>
      </div>
      <div>
        <div style="font-weight:800;font-size:13px;color:#F5883E;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:16px">Contact</div>''',
    "footer catalogue column")

# --- 7. route the real navigation at the static catalogue --------------------
# Without this the pages under /products/ are live but unreachable: the nav
# "Products" control, the hero CTA and all 20 category cards are onClick
# handlers that open the in-page view instead, leaving the footer as the only
# way in. Point every one of them at a real URL.

# nav (desktop), mobile nav, footer: three <button onClick="{{ openProducts...
for _old, _new in [
    ('<button onClick="{{ openProducts }}" style="background:none;border:none;padding:0;font-family:inherit;cursor:pointer;color:#081B33D1;font-weight:600;font-size:15px" style-hover="color:#F5883E">Products</button>',
     '<a href="/products/" style="text-decoration:none;color:#081B33D1;font-weight:600;font-size:15px" style-hover="color:#F5883E">Products</a>'),
    ('<button onClick="{{ openProductsMobile }}" style="background:none;border:none;padding:0;text-align:left;font-family:inherit;cursor:pointer;color:#081B33;font-weight:700;font-size:16px">Products</button>',
     '<a href="/products/" style="text-decoration:none;color:#081B33;font-weight:700;font-size:16px">Products</a>'),
    ('<button onClick="{{ openProducts }}" style="background:none;border:none;padding:0;text-align:left;font-family:inherit;cursor:pointer;color:rgba(255,255,255,0.6);font-size:14.5px" style-hover="color:#fff">Products</button>',
     '<a href="/products/" style="text-decoration:none;color:rgba(255,255,255,0.6);font-size:14.5px" style-hover="color:#fff">Products</a>'),
]:
    sub(_old, _new, "Products control")


# --- 8. drop the unreachable in-page catalogue view -------------------------
# Nothing opens it since the navigation was pointed at /products/, but it still
# shipped ~14KB of markup carrying 55 unrendered {{ }} tokens and a second <h1>
# that a non-JS crawler reads as page content.
_start = src.index("  <!-- PRODUCTS PAGE -->")
_end = src.index("  <!-- FOOTER -->")
_dead = src[_start:_end]
if not (10000 < len(_dead) < 20000 and "showProducts" in _dead):
    sys.exit("products-page block looks wrong (%d bytes); refusing to cut" % len(_dead))
src = src[:_start] + src[_end:]

# --- 9. mobile layout -------------------------------------------------------
# The design carries no media queries at all, so at 375px the desktop nav
# overflows (543px of links in a 375px viewport, "Call Now" clipped off-screen)
# while the hamburger the design already ships sits at display:none, and every
# grid keeps its desktop column count - 5 brand logos across 311px, 20 category
# cards at 4 across. Everything below is inside a media query, so the desktop
# rendering is byte-for-byte unchanged.

# The grids are inline-styled and otherwise unaddressable, so tag each one.
# Contact already carries .be-contact-grid from the design.
for _cls, _needle in [
    ("be-stats", "grid-template-columns:repeat(4,1fr);gap:32px"),
    ("be-about", "grid-template-columns:1fr 1fr;gap:24px 32px"),
    ("be-services", "grid-template-columns:repeat(3,1fr);gap:1px"),
    ("be-brands", "grid-template-columns:repeat(5,1fr);border-top:1px solid #E7E2D6"),
    ("be-footer", "grid-template-columns:1.3fr 0.8fr 1fr 1fr"),
]:
    _i = src.find(_needle)
    if _i == -1:
        sys.exit("mobile: could not find the grid for ." + _cls)
    _tag = src.rfind("<div", 0, _i)
    if 'class="' in src[_tag:_i]:
        sys.exit("mobile: ." + _cls + " target already has a class attribute")
    src = src[:_tag + 4] + ' class="%s"' % _cls + src[_tag + 4:]

# Tag the real content wrappers. Every one carries a max-width; the three
# decorative absolutely-positioned layers do not - and a blanket
# "section > div" padding rule reaches those too, which inflated the hero's
# 2px accent line into a 90px orange band. .be-pad is the subset whose
# vertical padding is big enough to be worth trimming on a phone, so the
# header and the footer bar keep their tight spacing.
_wrap = re.compile(r'<div([^>]*?)style="([^"]*?max-width:1\d{3}px[^"]*)"')


def _tag_wrap(m):
    attrs, style = m.group(1), m.group(2)
    classes = ["be-wrap"]
    _pad = re.search(r"padding:\s*(\d+)px", style)
    if _pad and int(_pad.group(1)) >= 56:
        classes.append("be-pad")
    joined = " ".join(classes)
    if 'class="' in attrs:
        attrs = attrs.replace('class="', 'class="%s ' % joined, 1)
    else:
        attrs = ' class="%s"' % joined + attrs
    return '<div%sstyle="%s"' % (attrs, style)


src, _n = _wrap.subn(_tag_wrap, src)
if _n != 11:
    sys.exit("mobile: expected 11 content wrappers, tagged %d" % _n)

sub("</style>", """
    /* ---------- mobile. Nothing here applies above 860px. ---------- */
    @media (max-width: 860px) {
      .be-nav-desktop { display: none !important; }
      .be-nav-toggle { display: block !important; }
      .be-services { grid-template-columns: repeat(2, 1fr) !important; }
      .be-about, .be-contact-grid { grid-template-columns: 1fr !important; }
      .be-footer { grid-template-columns: 1fr 1fr !important; }
      .be-brands { grid-template-columns: repeat(4, 1fr) !important; }
      .be-wrap { padding-left: 20px !important; padding-right: 20px !important; }
      .be-contact-grid { gap: 40px !important; }
    }
    @media (max-width: 560px) {
      .be-stats { grid-template-columns: repeat(2, 1fr) !important; }
      .be-services, .be-footer { grid-template-columns: 1fr !important; }
      .be-brands { grid-template-columns: repeat(3, 1fr) !important; }
      /* the desktop vertical rhythm is dead scrolling on a phone */
      .be-pad { padding-top: 52px !important; padding-bottom: 38px !important; }
    }
  </style>""", "mobile stylesheet")

# --- 10. industry segment pages ----------------------------------------------
# /industries/ is generated separately (build/build.js) and is the main internal
# linking surface into /products/. Without this step the eight segment pages are
# live but unreachable from the home page: the segment grid is six hard-coded
# <div>s with no links and the wrong six segments.

sub('''    const industryList = [
      { name: "Manufacturing", desc: "Precision hand & power tools for production lines and workshops." },
      { name: "Construction", desc: "Rugged equipment built for on-site demands and heavy use." },
      { name: "Automotive", desc: "Torque wrenches, garage tools and service equipment." },
      { name: "Fabrication", desc: "Cutting, grinding and holding tools for metalwork." },
      { name: "Maintenance & MRO", desc: "Ready-stock consumables to keep operations running." },
      { name: "Dealers & Retail", desc: "Bulk supply and channel support for resellers." },
    ]''',
    '''    const industryList = [
      { name: "Automotive & Auto Components", desc: "Line-side tooling, torque control and breakdown cover for OEMs and tier suppliers.", href: "/industries/automotive-auto-components/" },
      { name: "Pharmaceutical & Life Sciences", desc: "Non-sparking, stainless and validated-spare tooling for formulation, API and packaging sites.", href: "/industries/pharmaceutical-life-sciences/" },
      { name: "Food, Beverage & Agro", desc: "Wash-down-durable tooling, H1 lubrication and seasonal stock planning for soya, poha, spice and packaged food plants.", href: "/industries/food-beverage-agro-processing/" },
      { name: "Engineering & Fabrication", desc: "Bench-to-dispatch fit-out, consumable reorder discipline and the full brand range on one counter.", href: "/industries/engineering-fabrication/" },
      { name: "Textiles & Garments", desc: "High-volume small-tool supply, machine-specific kits and lubrication programme support for spinning, weaving and processing.", href: "/industries/textiles-garments/" },
      { name: "Power & Electrical", desc: "Certified 1000V insulated tooling, cable termination kits and site-ready contractor sets.", href: "/industries/power-utilities-electrical/" },
      { name: "Construction & Infrastructure", desc: "Site delivery, loss-aware specification and IS-marked lifting equipment for contractors and developers.", href: "/industries/construction-infrastructure/" },
      { name: "Plastics, Packaging & Printing", desc: "Mould change kits, tool room precision and blade continuity for moulders, converters and printers.", href: "/industries/plastics-packaging-printing/" },
    ]''',
    "industry list")

# segment card: <div> -> <a href>
sub('''          <div style="background:#081B33;padding:34px 28px" style-hover="background:#0F2E52">
            <div style="font-family:'Big Shoulders Display',sans-serif;font-weight:800;font-size:15px;color:rgba(255,255,255,0.35);margin-bottom:10px">{{ ind.n }}</div>
            <div style="font-weight:800;font-size:19px;color:#fff;margin-bottom:8px">{{ ind.name }}</div>
            <div style="font-size:13.5px;color:rgba(255,255,255,0.55);line-height:1.5">{{ ind.desc }}</div>
          </div>''',
    '''          <a href="{{ ind.href }}" style="display:block;text-decoration:none;background:#081B33;padding:34px 28px" style-hover="background:#0F2E52">
            <div style="font-family:'Big Shoulders Display',sans-serif;font-weight:800;font-size:15px;color:rgba(255,255,255,0.35);margin-bottom:10px">{{ ind.n }}</div>
            <div style="font-weight:800;font-size:19px;color:#fff;margin-bottom:8px">{{ ind.name }}</div>
            <div style="font-size:13.5px;color:rgba(255,255,255,0.55);line-height:1.5">{{ ind.desc }}</div>
            <div style="font-size:12px;font-weight:700;color:#F5883E;letter-spacing:0.06em;text-transform:uppercase;margin-top:16px">Open the checklist &rarr;</div>
          </a>''',
    "segment card")

# nav: an Industries entry beside Products, in all three places
for _o, _n in [
    ('<a href="/products/" style="text-decoration:none;color:#081B33D1;font-weight:600;font-size:15px" style-hover="color:#F5883E">Products</a>',
     '<a href="/industries/" style="text-decoration:none;color:#081B33D1;font-weight:600;font-size:15px" style-hover="color:#F5883E">Industries</a>'
     '<a href="/products/" style="text-decoration:none;color:#081B33D1;font-weight:600;font-size:15px" style-hover="color:#F5883E">Products</a>'),
    ('<a href="/products/" style="text-decoration:none;color:#081B33;font-weight:700;font-size:16px">Products</a>',
     '<a href="/industries/" style="text-decoration:none;color:#081B33;font-weight:700;font-size:16px">Industries</a>'
     '<a href="/products/" style="text-decoration:none;color:#081B33;font-weight:700;font-size:16px">Products</a>'),
    ('<a href="/products/" style="text-decoration:none;color:rgba(255,255,255,0.6);font-size:14.5px" style-hover="color:#fff">Products</a>',
     '<a href="/industries/" style="text-decoration:none;color:rgba(255,255,255,0.6);font-size:14.5px" style-hover="color:#fff">Industries</a>'
     '<a href="/products/" style="text-decoration:none;color:rgba(255,255,255,0.6);font-size:14.5px" style-hover="color:#fff">Products</a>'),
]:
    sub(_o, _n, "Industries nav entry")

# --- 11. cache-bust email-protect.js -----------------------------------------
# /assets/* is served with a 24h Cache-Control, so a returning visitor's
# browser won't pick up a script fix until the referenced URL itself
# changes -- found this the hard way testing one. Content-hash query param,
# matching the convention build-catalogue-pages.py already uses for its own
# assets.
_em_hash = hashlib.md5((out.parent / "assets" / "email-protect.js").read_bytes()).hexdigest()[:8]
sub('<script src="/assets/email-protect.js" defer></script>',
    f'<script src="/assets/email-protect.js?v={_em_hash}" defer></script>',
    "email-protect.js cache-bust")

# --- 12. pre-render the constant list loops ---------------------------------
# The runtime renders <sc-for> client-side, so everything inside one is invisible
# to anything that does not run JavaScript. That left the shipped HTML carrying
# 45 literal "{{ }}" tokens where the hero figures, the stat band, the eight
# segment cards, the brand wall and all four phone numbers should be. Googlebot
# renders JS but defers it; GPTBot, ClaudeBot and PerplexityBot never do, so AI
# answers read the home page as broken template text.
#
# Every list below is a constant in renderVals(), so unrolling it at build time
# is a pure serialisation: the runtime re-parses the same markup and React
# produces the identical tree. Anything state-driven (<sc-if navOpen>, the
# products view, marqueeStyle) is deliberately left alone.

def _js_array(anchor, label):
    """Parse the JS array literal introduced by `anchor` into Python data."""
    i = src.find(anchor)
    if i == -1:
        sys.exit("prerender: could not find " + label)
    start = src.index("[", i)
    depth, end = 0, None
    for j in range(start, len(src)):
        if src[j] == "[":
            depth += 1
        elif src[j] == "]":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    if end is None:
        sys.exit("prerender: unterminated array for " + label)
    lit = src[start:end]
    lit = _re.sub(r'(?<=[{,])\s*([A-Za-z_]\w*)\s*:', r'"\1":', lit)  # bare keys
    lit = _re.sub(r",(\s*[}\]])", r"\1", lit)                        # trailing commas
    try:
        return _json.loads(lit)
    except ValueError as e:
        sys.exit("prerender: %s is not a plain literal (%s)" % (label, e))


def _esc(v):
    return (str(v).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _unroll(list_name, items, expect):
    """Replace the <sc-for> over `list_name` with its rendered rows."""
    global src
    if len(items) != expect:
        sys.exit("prerender: %s has %d rows, expected %d" % (list_name, len(items), expect))
    pat = _re.compile(
        r'[ \t]*<sc-for list="\{\{ %s \}\}" as="([A-Za-z_]\w*)"[^>]*>(.*?)</sc-for>'
        % _re.escape(list_name), _re.S)
    m = pat.search(src)
    if not m:
        sys.exit("prerender: no <sc-for> over " + list_name)
    var, body = m.group(1), m.group(2).strip("\n").rstrip()
    rows = []
    for item in items:
        row = body
        if isinstance(item, dict):
            for k, v in item.items():
                row = row.replace("{{ %s.%s }}" % (var, k), _esc(v))
        else:
            row = row.replace("{{ %s }}" % var, _esc(item))
        left = _re.findall(r"\{\{[^}]*\}\}", row)
        if left:
            sys.exit("prerender: %s left %s unrendered" % (list_name, left[0]))
        rows.append(row)
    src = src[:m.start()] + "\n".join(rows) + src[m.end():]


_industries = _js_array("const industryList = [", "industryList")
for _i, _it in enumerate(_industries):
    _it["n"] = "%02d" % (_i + 1)          # mirrors .map((it, i) => padStart(2, "0"))

_logos = _js_array("const brandLogos = [", "brandLogos")
for _b in _logos:
    _b["src"] = "assets/brands/" + _b["file"] + ".png"
    _b["logoStyle"] = ("width:100%;height:100%;background:url('assets/brands/"
                       + _b["file"] + ".png') center/contain no-repeat")

_brand_names = _js_array("const brandNames = [", "brandNames")

_before = src.count("{{")
_unroll("heroFacts",     _js_array("heroFacts: [", "heroFacts"),         3)
_unroll("stats",         _js_array("stats: [", "stats"),                 4)
_unroll("aboutPoints",   _js_array("aboutPoints: [", "aboutPoints"),     4)
_unroll("industries",    _industries,                                    8)
_unroll("customerTypes", _js_array("customerTypes: [", "customerTypes"), 3)
_unroll("brandsDoubled", _brand_names + _brand_names,                   50)
_unroll("brandLogos",    _logos,                                        25)
_unroll("phones",        _js_array("phones: [", "phones"),               4)

# What is left has to be attributes and handlers the runtime still owns, never
# page copy. Anything sitting in a text node would be read as content.
_template = src[src.index("<x-dc>"):src.index("</x-dc>")]
_visible = [t for t in _re.findall(r">[^<>]*(\{\{[^}]*\}\})[^<>]*<", _template)]
if _visible:
    sys.exit("prerender: %s still renders as page text" % _visible[0])
print("  pre-rendered 8 loops, %d -> %d {{ }} tokens" % (_before, src.count("{{")))

# --- 13. accessibility: contrast, form labels, skip link ---------------------
# Measured in the browser against the composited background, not eyeballed.
# Brand orange #F5883E reaches only 2.34:1 on the cream ground and 2.47:1 on the
# header white, so the four orange runs that sit on a light surface get a darker
# orange; the seventeen that sit on navy keep the brand colour and pass at 6.97.
# The faint whites on navy (0.35 and 0.4 alpha) came in at 3.18 and 3.75.

ORANGE_INK = "#B64F09"          # 4.82:1 on #FBF8F2, 5.11:1 on white

for _label in ("Tools &amp; Industrial Supply", "About Balaji Enterprises",
               "DEALERSHIPS", "Get In Touch"):
    _m = _re.search(r'<span style="([^"]*color:#F5883E[^"]*)">' + _re.escape(_label),
                    src)
    if not _m:
        sys.exit("a11y: could not find the orange run for " + _label)
    src = src.replace(_m.group(0),
                      _m.group(0).replace("color:#F5883E", "color:" + ORANGE_INK), 1)

for _old, _new, _want in (("0.35", "0.48", 8), ("0.4", "0.48", 2)):
    _pat = "color:rgba(255,255,255,%s)" % _old
    _n = src.count(_pat)
    if _n != _want:
        sys.exit("a11y: expected %d uses of %s, found %d" % (_want, _pat, _n))
    src = src.replace(_pat, "color:rgba(255,255,255,%s)" % _new)

# The quote form's labels were siblings with no `for`, and the inputs had no id,
# so a screen reader announced only the placeholder - which disappears on input.
for _text, _ref, _id in (
    ("Full Name",              "nameRef",    "q-name"),
    ("Company / Organisation", "companyRef", "q-company"),
    ("Phone / Email",          "contactRef", "q-contact"),
    ("What do you need?",      "messageRef", "q-message"),
):
    _lab = '>%s</label>' % _text
    if src.count(_lab) != 1:
        sys.exit("a11y: label %r is not unique" % _text)
    # attach for= to this label specifically
    _i = src.index(_lab)
    _open = src.rindex("<label ", 0, _i)
    src = src[:_open] + '<label for="%s" ' % _id + src[_open + len("<label "):]
    # and id= to the matching field
    _fld = '{{ %s }}"' % _ref
    if src.count(_fld) != 1:
        sys.exit("a11y: field ref %r is not unique" % _ref)
    _j = src.index(_fld)
    _tagopen = src.rindex("<", 0, _j)
    _tagend = src.index(" ", _tagopen)
    src = src[:_tagend] + ' id="%s"' % _id + src[_tagend:]

# Skip link. The catalogue pages already ship one; the home page did not, and
# its nav is 6 links deep before any content.
sub("<x-dc>", '<x-dc>\n<a class="skip" href="#top">Skip to content</a>', "skip link")
sub("    html { scroll-behavior: smooth; }",
    """    html { scroll-behavior: smooth; }
    .skip { position: absolute; left: -9999px; top: 0; background: #F5883E;
            color: #081B33; padding: 10px 16px; font-weight: 800; z-index: 200; }
    .skip:focus { left: 8px; top: 8px; }
    :focus-visible { outline: 2px solid #F5883E; outline-offset: 2px; }""",
    "skip-link and focus styles")
# Privacy and terms are generated by build-catalogue-pages.py; every page has
# to link them or they are unreachable from the home page.
sub('<span style="font-size:13px;color:rgba(255,255,255,0.48)">rbalajient.com</span>',
    '<span style="font-size:13px;display:inline-flex;gap:18px">'
    '<a href="/privacy/" style="color:rgba(255,255,255,0.72);text-decoration:none">Privacy Policy</a>'
    '<a href="/terms/" style="color:rgba(255,255,255,0.72);text-decoration:none">Terms &amp; Conditions</a>'
    '</span>\n'
    '      <span style="font-size:13px;color:rgba(255,255,255,0.48)">rbalajient.com</span>',
    "footer legal links")
print("  a11y: 4 orange runs darkened, 10 faint whites raised, 4 labels bound, skip link added")

out.write_text(src)
print("wrote", out, len(src), "bytes")
