#!/usr/bin/env python3
"""Generate static, indexable catalogue pages from catalogue.js.

The single-page app keeps the whole catalogue in client-side state, so none of
it has a URL and none of it can be indexed. This writes a real page per
category and per product type, from the same data the app renders:

    /products/                          catalogue hub, all categories
    /products/<category>/               category: subcategories and their types
    /products/<category>/<product>/     product type: brand-by-brand specs

Run after any change to catalogue.js:

    python3 build-catalogue-pages.py

It rebuilds the products/ tree and sitemap.xml from scratch, so a product
removed from catalogue.js loses its page too.
"""

import html
import json
import pathlib
import re
import hashlib
import shutil

ROOT = pathlib.Path(__file__).parent
SITE = "https://www.rbalajient.com"
OUT = ROOT / "products"
PHOTOS = ROOT / "assets" / "products"

# Written by build/build.js alongside the /industries/ pages: which segments
# reference each product type, and the segment-specific note for it. Renders as
# the reverse of the industry -> product linking, so the two directions stay in
# step without this script re-deriving any of it. Absent = no strips, no error.
_map_file = ROOT / "industries-map.json"
INDUSTRY_MAP = json.loads(_map_file.read_text()) if _map_file.exists() else {}

PHONE = "9302110344"
SALES = "sales@rbalajient.com"
ADDRESS = "118 Siyaganj Main Road, Indore, 452007 (MP)"


# Assets are served with max-age=86400, so a plain /assets/catalogue.css would
# keep returning visitors on the previous build for up to a day. Every
# reference carries a content hash instead: the cache stays aggressive and a
# changed file is a changed URL, so updates land immediately.
VER = {"css": "0", "js": "0", "idx": "0", "em": "0"}


def digest(*parts):
    h = hashlib.md5()
    for x in parts:
        h.update(x if isinstance(x, bytes) else str(x).encode())
    return h.hexdigest()[:8]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def e(s):
    return html.escape(str(s), quote=True)



def num(n):
    return f"{n:,}"


# Google truncates titles near 60 chars and snippets near 155. Rather than a
# single template that overflows on long product names, try progressively
# shorter forms and take the first that fits, so short names keep the local
# keyword and only the longest lose it.
TITLE_CAP = 60
DESC_CAP = 155


def fit(candidates, cap):
    for c in candidates:
        if len(c) <= cap:
            return c
    return candidates[-1]


def photo_for(name):
    for ext in ("jpg", "png"):
        if (PHOTOS / f"{slug(name)}.{ext}").exists():
            return f"/assets/products/{slug(name)}.{ext}"
    return None


# --------------------------------------------------------------------------
# shared chrome
# --------------------------------------------------------------------------

def head(title, desc, canonical, jsonld, robots="index, follow, max-image-preview:large, max-snippet:-1"):
    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#081B33">
<link rel="icon" href="/assets/logo.png" type="image/png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Balaji Enterprises">
<meta property="og:locale" content="en_IN">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/logo.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800;900&family=Manrope:wght@400;500;600;700;800&display=swap">
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800;900&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800;900&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet"></noscript>
<link rel="stylesheet" href="/assets/catalogue.css?v={VER['css']}">
<script type="application/ld+json">{jsonld}</script>
<script src="/assets/email-protect.js?v={VER['em']}" defer></script>
<script src="/assets/catalogue-ui.js?v={VER['js']}" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a href="/" class="brand">
      <img src="/assets/logo.png" alt="" width="40" height="40">
      <span class="brand-text"><b>BALAJI ENTERPRISES</b><i>Tools &amp; Industrial Supply</i></span>
    </a>
    <nav class="site-nav">
      <a href="/products/">Products</a>
      <a href="/industries/">Industries</a>
      <a href="/#about">About</a>
      <a href="/#contact">Contact</a>
      <a href="tel:{PHONE}" class="btn-call">Call Now</a>
    </nav>
  </div>
</header>
"""


def footer(cats):
    links = "".join(
        f'<li><a href="/products/{c["slug"]}/">{e(c["name"])}</a></li>' for c in cats)
    return f"""
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <div class="footer-brand">
        <img src="/assets/logo.png" alt="" width="36" height="36">
        <span>BALAJI ENTERPRISES</span>
      </div>
      <p>Authorised distributor of hand tools, power tools and industrial MRO
      equipment, based in Indore, Madhya Pradesh since 1996.</p>
      <a class="footer-social" href="https://www.linkedin.com/company/rbalajient/" target="_blank" rel="noopener" aria-label="Balaji Enterprises on LinkedIn"><svg viewBox="0 0 448 512" width="18" height="18" aria-hidden="true" focusable="false"><path fill="currentColor" d="M100.28 448H7.4V148.9h92.88zM53.79 108.1C24.09 108.1 0 83.5 0 53.8a53.79 53.79 0 0 1 107.58 0c0 29.7-24.1 54.3-53.79 54.3zM447.9 448h-92.68V302.4c0-34.7-.7-79.3-48.29-79.3-48.29 0-55.7 37.7-55.7 76.7V448h-92.78V148.9h89.08v40.8h1.3c12.4-23.5 42.7-48.3 87.9-48.3 94 0 111.28 61.9 111.28 142.3V448z"/></svg></a>
    </div>
    <div>
      <h2 class="footer-h">Catalogue</h2>
      <ul class="footer-list">{links}</ul>
    </div>
    <div>
      <h2 class="footer-h">Contact</h2>
      <ul class="footer-list">
        <li>{ADDRESS}</li>
        <li><a href="tel:{PHONE}">{PHONE}</a></li>
        <li><a href="javascript:void(0)" data-em="c2FsZXNAcmJhbGFqaWVudC5jb20=" class="js-email-text">sales [at] rbalajient.com</a></li>
        <li>Mon&ndash;Sat 10:00&ndash;19:30</li>
      </ul>
    </div>
  </div>
  <div class="wrap footer-bar">
    <span>&copy; 2026 Balaji Enterprises. All rights reserved.</span>
    <span class="footer-legal"><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms &amp; Conditions</a></span>
    <span>rbalajient.com</span>
  </div>
</footer>
</body>
</html>
"""


def search_box():
    return f"""
    <div class="search-box" data-search data-index-v="{VER['idx']}" hidden>
      <label class="sr-only" for="cat-q">Search products and part numbers</label>
      <input id="cat-q" type="search" autocomplete="off" role="combobox"
             aria-expanded="false" aria-controls="cat-results"
             placeholder="Search 243 products or a part number\u2026">
      <div class="search-results" id="cat-results" data-results role="listbox" hidden></div>
    </div>"""


def crumbs(trail):
    """trail: [(label, href|None)]; the last entry is the current page."""
    parts, items = [], []
    for i, (label, href) in enumerate(trail):
        if href:
            parts.append(f'<a href="{href}">{e(label)}</a>')
            items.append({"@type": "ListItem", "position": i + 1,
                          "name": label, "item": SITE + href})
        else:
            parts.append(f"<span>{e(label)}</span>")
            items.append({"@type": "ListItem", "position": i + 1, "name": label})
    nav = ('<nav class="crumbs" aria-label="Breadcrumb">'
           + '<span class="sep">/</span>'.join(parts) + "</nav>")
    return nav, {"@type": "BreadcrumbList", "itemListElement": items}


def ld(*nodes):
    return json.dumps({"@context": "https://schema.org", "@graph": list(nodes)},
                      ensure_ascii=False)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --------------------------------------------------------------------------
# page builders
# --------------------------------------------------------------------------

def product_page(cat, sub, name, groups, sibs, url, cats):
    """groups: [(cols, brands)]; more than one only where the source data holds
    two type entries under the same name in the same category."""
    photo = photo_for(name)
    brands = sorted({b["name"] for _, bs in groups for b in bs})
    n_rows = sum(len(b["rows"]) for _, bs in groups for b in bs)

    unit = "size" if n_rows == 1 else "sizes"
    meta_desc = fit(
        [f"{name}: {num(n_rows)} {unit} and part numbers from "
         f"{', '.join(brands[:k])}{' and more' if k < len(brands) else ''}, with "
         f"specifications and list prices. Ready stock in Indore."
         for k in range(len(brands), 0, -1)]
        + [f"{name}: {num(n_rows)} {unit} and part numbers with specifications "
           f"and list prices. Ready stock from Balaji Enterprises, Indore."],
        DESC_CAP)

    crumb_nav, crumb_ld = crumbs([
        ("Home", "/"), ("Products", "/products/"),
        (cat["name"], f'/products/{cat["slug"]}/'), (name, None)])

    prod_ld = {"@type": "Product", "name": name,
               "category": f'{cat["name"]} > {sub}',
               "brand": [{"@type": "Brand", "name": b} for b in brands],
               "url": SITE + url}
    prod_ld["description"] = meta_desc
    if photo:
        prod_ld["image"] = SITE + photo

    tables = []
    for cols, bs in groups:
        for b in sorted(bs, key=lambda x: -len(x["rows"])):
            ths = "".join(f"<th>{e(c)}</th>" for c in cols)
            rows = []
            for row in b["rows"]:
                tds = "".join(
                    ('<td class="pn">' if i == 0 else "<td>") + e(v) + "</td>"
                    for i, v in enumerate(row))
                rows.append(f"<tr>{tds}</tr>")
            n = len(b["rows"])
            tables.append(f"""
    <section class="brand-block">
      <h2 class="brand-name">{e(b["name"])}<span class="brand-count">{num(n)} size{"s" if n != 1 else ""}</span></h2>
      <div class="table-scroll">
        <table>
          <caption class="sr-only">{e(name)} &mdash; {e(b["name"])} sizes, part numbers and list prices</caption>
          <thead><tr>{ths}</tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </section>""")

    used = ""
    _segs = INDUSTRY_MAP.get(url, [])
    if _segs:
        cards = "".join(
            f'<li><a href="{sg["href"]}"><span class="used-n">{e(sg["n"])}</span>'
            f'<span class="used-name">{e(sg["name"])}</span>'
            f'<span class="used-note">{e(sg["note"])}</span></a></li>'
            for sg in _segs)
        used = f"""
    <section class="used-in">
      <h2>Used in these industries</h2>
      <p class="used-lead">Where {e(name)} shows up on the shop floor, and what it is
      doing there. Each page carries the full tool and MRO checklist for that plant.</p>
      <ul class="used-grid">{cards}</ul>
    </section>"""

    rel = ""
    if sibs:
        items = "".join(f'<li><a href="{u}">{e(n)}</a></li>' for n, u in sibs)
        rel = f"""
    <section class="related">
      <h2>More in {e(sub)}</h2>
      <ul class="pill-list">{items}</ul>
    </section>"""

    # Raw (not percent-encoded) text: email-protect.js runs encodeURIComponent
    # itself when it builds the mailto: at hydration time. e() still has to
    # HTML-escape it for the attribute (a product name with "&" -- Abrasive
    # Disc & Paper -- would otherwise break the attribute).
    subject = e(f"Quote request: {name}")
    body = e(f"Please send current pricing and availability for {name}.\n\n"
             "Sizes / part numbers needed:\n")

    hero = (f'<div class="prod-photo"><img src="{photo}" alt="{e(name)} supplied by '
            f'Balaji Enterprises, Indore" width="300" height="300"></div>'
            if photo else
            '<div class="prod-photo no-photo"><span>Photo on request</span></div>')

    title = fit([
        f"{name}: {num(n_rows)} Sizes & Prices | Balaji Enterprises Indore",
        f"{name}: {num(n_rows)} Sizes & Prices | Balaji Enterprises",
        f"{name}: {num(n_rows)} Sizes | Balaji Enterprises",
        f"{name} | Balaji Enterprises Indore",
        f"{name} | Balaji Enterprises",
    ], TITLE_CAP)

    return head(title, meta_desc, SITE + url, ld(prod_ld, crumb_ld)) + f"""
<main id="main">
  <div class="wrap">
    {crumb_nav}
    <div class="prod-head">
      {hero}
      <div class="prod-intro">
        <span class="eyebrow">{e(cat["name"])} &middot; {e(sub)}</span>
        <h1>{e(name)}</h1>
        <p class="meta">{num(n_rows)} listed size{"s" if n_rows != 1 else ""} &amp; part numbers &middot; {len(brands)} brand{"s" if len(brands) != 1 else ""}</p>
        <ul class="brand-chips">{"".join(f"<li>{e(b)}</li>" for b in brands)}</ul>
        <div class="cta-row">
          <a class="btn-primary" href="javascript:void(0)" data-em="c2FsZXNAcmJhbGFqaWVudC5jb20=" data-subject="{subject}" data-body="{body}">Request a Quote</a>
        </div>
      </div>
    </div>
    <h2 class="specs-h">Sizes, part numbers &amp; specifications</h2>
    <p class="specs-note">Listed brand by brand. Prices are list prices in INR and
    exclude taxes &mdash; contact us for current trade pricing and availability.</p>
    <div class="spec-filter" data-spec-filter hidden></div>
    {"".join(tables)}
    {used}
    {rel}
  </div>
</main>
""" + footer(cats)


def category_page(cat, types_by_sub, url, cats, card_brands):
    n_types = sum(len(v[1]) for v in types_by_sub.values())
    n_items = sum(r for v in types_by_sub.values() for _, _, r in v[1])

    crumb_nav, crumb_ld = crumbs([
        ("Home", "/"), ("Products", "/products/"), (cat["name"], None)])

    listed, blocks, pos = [], [], 0
    for sub, (sub_slug, entries) in types_by_sub.items():
        cards = []
        for name, u, rows in entries:
            pos += 1
            listed.append({"@type": "ListItem", "position": pos,
                           "name": name, "url": SITE + u})
            ph = photo_for(name)
            thumb = (f'<img src="{ph}" alt="" loading="lazy" width="64" height="64">'
                     if ph else '<span class="thumb-blank" aria-hidden="true"></span>')
            cards.append(f"""
        <li class="type-card" data-brands="{e(card_brands.get(name, ""))}"><a href="{u}">{thumb}
          <span class="type-name">{e(name)}</span>
          <span class="type-meta">{num(rows)} size{"s" if rows != 1 else ""}</span></a></li>""")
        blocks.append(f"""
    <section class="sub-block" id="{sub_slug}">
      <h2>{e(sub)}</h2>
      <ul class="type-grid">{"".join(cards)}</ul>
    </section>""")

    page_ld = {"@type": "CollectionPage",
               "name": f'{cat["name"]} | Balaji Enterprises',
               "url": SITE + url,
               "mainEntity": {"@type": "ItemList", "numberOfItems": n_types,
                              "itemListElement": listed}}

    desc = fit([
        f'{cat["name"]} in Indore: {n_types} product types, {num(n_items)} listed '
        "sizes and part numbers with specifications and list prices. Authorised "
        "distributor, ready stock since 1996.",
        f'{cat["name"]} in Indore: {n_types} product types, {num(n_items)} sizes '
        "and part numbers with specs and list prices. Authorised distributor since 1996.",
        f'{cat["name"]} in Indore: {n_types} product types, {num(n_items)} sizes '
        "with specs and list prices. Balaji Enterprises, since 1996.",
    ], DESC_CAP)

    title = fit([
        f'{cat["name"]} Supplier in Indore | Balaji Enterprises',
        f'{cat["name"]} in Indore | Balaji Enterprises',
        f'{cat["name"]} | Balaji Enterprises',
    ], TITLE_CAP)

    return head(title, desc, SITE + url, ld(page_ld, crumb_ld)) + f"""
<main id="main">
  <div class="wrap">
    {crumb_nav}
    <div class="page-head">
      <span class="eyebrow">Product Catalogue</span>
      <h1>{e(cat["name"])}</h1>
      <p class="lead">{num(n_types)} product types &middot; {num(n_items)} listed sizes &amp;
      part numbers. Every product lists the brands we stock for it, with
      specifications set out brand by brand.</p>
    </div>
    {search_box()}
    <div class="filter-bar" data-brand-filter hidden></div>
    {"".join(blocks)}
  </div>
</main>
""" + footer(cats)


# One real product photo per category, picked by hand for what reads clearly
# at thumbnail size and represents the category well -- not just the biggest
# product type. Falls back to no image (handled in hub_page) if a file is
# ever missing.
CAT_PHOTOS = {
    "hand-tools": "adjustable-wrench",
    "cutting-tools-abrasives": "abrasive-disc-paper",
    "tool-storage-workshop": "tool-box",
    "lubrication-fluid-handling": "grease-gun",
    "measuring-layout": "vernier-caliper",
    "power-tools": "angle-grinder",
    "lifting-pulling": "hydraulic-bottle-jack",
    "material-handling": "hand-truck-trolley",
}


def hub_page(cats, counts, url="/products/"):
    crumb_nav, crumb_ld = crumbs([("Home", "/"), ("Products", None)])
    cards, listed = [], []
    for i, c in enumerate(cats):
        n_types, n_items = counts[c["slug"]]
        listed.append({"@type": "ListItem", "position": i + 1, "name": c["name"],
                       "url": f'{SITE}/products/{c["slug"]}/'})
        photo_slug = CAT_PHOTOS.get(c["slug"])
        photo = (f'<img src="/assets/products/{photo_slug}.jpg" alt="" loading="lazy" '
                 f'width="200" height="200">' if photo_slug else "")
        cards.append(f"""
      <li class="cat-card"><a href="/products/{c["slug"]}/">
        <span class="cat-photo">{photo}</span>
        <span class="cat-body">
          <span class="cat-n">{i + 1:02d}</span>
          <span class="cat-name">{e(c["name"])}</span>
          <span class="cat-meta">{n_types} product types &middot; {num(n_items)} sizes</span>
          <span class="cat-go">View products &rarr;</span>
        </span></a></li>""")

    total = sum(v[1] for v in counts.values())
    page_ld = {"@type": "CollectionPage",
               "name": "Product Catalogue | Balaji Enterprises", "url": SITE + url,
               "mainEntity": {"@type": "ItemList", "numberOfItems": len(cats),
                              "itemListElement": listed}}

    return head("Tool & MRO Catalogue | Balaji Enterprises Indore",
                fit([f"Browse {num(total)} tool and MRO listings across {len(cats)} "
                     "categories: hand tools, power tools, measuring instruments and "
                     "abrasives, with sizes, part numbers and list prices. Indore.",
                     f"Browse {num(total)} tool and MRO listings across {len(cats)} "
                     "categories, with sizes, part numbers and list prices. "
                     "Balaji Enterprises, Indore."], DESC_CAP),
                SITE + url, ld(page_ld, crumb_ld)) + f"""
<main id="main">
  <div class="wrap">
    {crumb_nav}
    <div class="page-head">
      <span class="eyebrow">Product Catalogue</span>
      <h1>Every tool, every specification.</h1>
      <p class="lead">{num(total)} listed sizes and part numbers across {len(cats)}
      categories. Each product lists the brands we stock for it, with
      specifications set out brand by brand so procurement teams can compare and
      order directly.</p>
    </div>
    {search_box()}
    <ul class="cat-grid">{"".join(cards)}</ul>
  </div>
</main>
""" + footer(cats)


def not_found_page(cats):
    """The custom 404 -- Vercel's static builder serves this automatically
    for any unmatched path, with a real 404 status (not a redirect to /)."""
    quick = "".join(
        f'<a href="/products/{c["slug"]}/">{e(c["name"])}</a>' for c in cats)

    page_ld = {"@type": "WebPage", "name": "Page Not Found",
               "url": SITE + "/404.html",
               "isPartOf": {"@type": "WebSite", "name": "Balaji Enterprises", "url": SITE}}

    return head("Page Not Found | Balaji Enterprises",
                "That page doesn't exist or has moved. Browse the tool and MRO "
                "catalogue or get in touch -- Balaji Enterprises, Indore.",
                SITE + "/404.html", ld(page_ld),
                robots="noindex, follow") + f"""
<main id="main">
  <div class="wrap error-page">
    <p class="error-code">404</p>
    <h1 class="error-title">That page took a wrong turn.</h1>
    <p class="error-lead">The link's broken, or the page has moved. The catalogue and
    the rest of the site are one click away.</p>
    <div class="error-actions">
      <a class="btn-primary" href="/">Home</a>
      <a class="btn-outline" href="/products/">Browse the Catalogue</a>
      <a class="btn-outline" href="/industries/">Industries We Serve</a>
    </div>
    <div class="error-links">
      <h2>Or jump straight to a category</h2>
      <div class="error-link-grid">{quick}</div>
    </div>
  </div>
</main>
""" + footer(cats)


# --------------------------------------------------------------------------

LEGAL_UPDATED = "6 September 2026"


def legal_page(title, desc, url, heading, standfirst, sections, cats):
    """A plain prose page (privacy, terms). Same shell as everything else."""
    body = "".join(
        f'\n    <h2>{h}</h2>\n    ' + "\n    ".join(p for p in paras)
        for h, paras in sections)
    page_ld = {"@type": "WebPage", "name": heading, "url": SITE + url,
               "isPartOf": {"@type": "WebSite", "name": "Balaji Enterprises", "url": SITE}}
    return head(title, desc, SITE + url, ld(page_ld)) + f"""
<main id="main">
  <div class="wrap legal">
    <h1>{heading}</h1>
    <p class="legal-lead">{standfirst}</p>
    <p class="legal-updated">Last updated: {LEGAL_UPDATED}</p>{body}
  </div>
</main>
""" + footer(cats)


def privacy_page(cats):
    P = lambda *xs: [f"<p>{x}</p>" for x in xs]
    return legal_page(
        "Privacy Policy | Balaji Enterprises",
        "How Balaji Enterprises handles personal data on rbalajient.com. No "
        "cookies, no tracking, and no data collected by this website.",
        "/privacy/", "Privacy Policy",
        "This website collects nothing about you. That is not a turn of phrase, "
        "and the sections below set out exactly what that means.",
        [
          ("Who we are", P(
            "Balaji Enterprises, 118 Siyaganj Main Road, Siyaganj, Indore, Madhya "
            "Pradesh 452007, India. For anything in this policy, write to "
            "<a href=\"javascript:void(0)\" data-em=\"c2FsZXNAcmJhbGFqaWVudC5jb20=\" class=\"js-email-text\">sales [at] rbalajient.com</a> "
            "or call <a href=\"tel:9302110344\">+91 93021 10344</a>.")),
          ("What this website collects", P(
            "Nothing. This site sets no cookies, uses no analytics, no advertising "
            "pixels and no tracking of any kind. It does not store anything in your "
            "browser, and it has no database or account system. There is nothing to "
            "opt into and nothing to opt out of, which is why you were not asked to "
            "accept cookies.")),
          ("The quote form", P(
            "The enquiry form does not send anything to us over the internet. When "
            "you press Send Enquiry, your own email program opens with a message "
            "already written out, addressed to our sales inbox. Nothing leaves your "
            "device unless you then choose to send that email yourself, and you can "
            "edit or discard it first.",
            "If you do send it, we receive an ordinary email containing whatever you "
            "typed. We use it to answer your enquiry and to keep the normal business "
            "records of a supplier and its customers. We do not sell it, rent it, or "
            "pass it to anyone for marketing.")),
          ("Information handled by others", P(
            "Two things happen that are outside our control and worth naming.",
            "<strong>Typefaces.</strong> Pages load fonts from Google Fonts. To "
            "deliver them, Google receives your IP address and basic request "
            "information. We have no access to that data.",
            "<strong>Hosting.</strong> The site is hosted by Vercel, which keeps "
            "standard server logs (including IP addresses) to serve pages and protect "
            "against abuse. We do not use those logs to identify visitors.")),
          ("Links to other places", P(
            "The site links out to LinkedIn, Google Maps and our catalogue QR page at "
            "taponn.me. Once you follow one of those links you are on someone else's "
            "website, under their privacy policy, not this one.")),
          ("Your rights", P(
            "Under India's Digital Personal Data Protection Act, 2023 you may ask what "
            "personal data of yours we hold, ask us to correct it, and ask us to erase "
            "it. If you are in the UK or the European Economic Area, the equivalent "
            "rights under the UK GDPR and GDPR apply.",
            "Because this website collects nothing, any request will concern emails or "
            "orders you sent us directly. Write to our sales address and we will "
            "respond within a reasonable period.")),
          ("Keeping information", P(
            "Enquiry emails and order records are kept for as long as we need them for "
            "the business relationship and for the periods Indian tax and company law "
            "require. After that they are deleted.")),
          ("Children", P(
            "This is a business-to-business supply site and is not directed at "
            "children. We do not knowingly collect data about anyone under 18.")),
          ("Changes", P(
            "If this policy changes, the revised version appears on this page with a "
            "new date at the top.")),
        ], cats)


def terms_page(cats):
    P = lambda *xs: [f"<p>{x}</p>" for x in xs]
    return legal_page(
        "Terms and Conditions | Balaji Enterprises",
        "Terms of use for rbalajient.com: catalogue accuracy, pricing, "
        "trademarks and governing law. Balaji Enterprises, Indore.",
        "/terms/", "Terms and Conditions",
        "These terms cover your use of this website. They do not replace the "
        "terms of any quotation, order or invoice we agree with you separately.",
        [
          ("Using this site", P(
            "You are welcome to browse the catalogue, print it and share it. You may "
            "not copy the site wholesale, scrape it in bulk, or republish it as your "
            "own. Please do not attempt to disrupt or gain unauthorised access to it.")),
          ("The catalogue is information, not an offer", P(
            "The product listings describe what we typically supply. They are an "
            "invitation to enquire, not a binding offer to sell. A sale exists only "
            "once we have confirmed your order in writing.")),
          ("Prices, sizes and availability", P(
            "Prices shown are indicative list prices in Indian Rupees and exclude GST, "
            "freight and any other charges unless we say otherwise. They change without "
            "notice. Sizes, part numbers and specifications come from manufacturer "
            "information and may be revised by the manufacturer at any time.",
            "Stock is not guaranteed by anything on this site. Please confirm current "
            "price and availability with us before relying on either.")),
          ("Brands and trademarks", P(
            "Balaji Enterprises is a distributor and channel partner. Every brand name, "
            "logo and product image on this site belongs to its respective owner, and "
            "appears here only to identify the goods we supply. Nothing on this site "
            "should be read as a claim of ownership of those marks, or as those brands "
            "endorsing this website.")),
          ("Accuracy", P(
            "We take care to keep the catalogue correct, but we do not warrant that it "
            "is complete, current or free of error. Product suitability for a particular "
            "job is a decision for you and your engineers; where safety is involved, "
            "follow the manufacturer's own instructions and the applicable standard.")),
          ("Liability", P(
            "To the extent the law allows, we are not liable for indirect or "
            "consequential loss arising from use of this website, or from reliance on "
            "information published on it. Nothing here limits liability that cannot "
            "lawfully be limited.")),
          ("Other websites", P(
            "Links to third-party sites are provided for convenience. We are not "
            "responsible for their content, products or practices.")),
          ("Governing law", P(
            "These terms are governed by the laws of India, and the courts at Indore, "
            "Madhya Pradesh have exclusive jurisdiction over any dispute.")),
          ("Contact", P(
            "Balaji Enterprises, 118 Siyaganj Main Road, Siyaganj, Indore, Madhya "
            "Pradesh 452007. Telephone <a href=\"tel:9302110344\">+91 93021 10344</a>, "
            "email <a href=\"javascript:void(0)\" data-em=\"c2FsZXNAcmJhbGFqaWVudC5jb20=\" class=\"js-email-text\">sales [at] rbalajient.com</a>.")),
        ], cats)


def main():
    raw = (ROOT / "catalogue.js").read_text()
    data = json.loads(raw[raw.index("{"):].rstrip().rstrip(";"))
    cats = data["cats"]

    if OUT.exists():
        shutil.rmtree(OUT)

    # Search indexes first: pages embed their version, so they must exist and be
    # hashed before a single page is written. Products are tiny and load with
    # the page; part numbers are an order of magnitude bigger, so
    # catalogue-ui.js fetches that one only once someone types a digit.
    prod_index, part_index, seen_u = [], [], set()
    for cat in cats:
        for sub in cat["subs"]:
            for t in sub["types"]:
                u = f'/products/{cat["slug"]}/{slug(t["name"])}/'
                if u not in seen_u:
                    seen_u.add(u)
                    prod_index.append({"n": t["name"], "u": u, "c": cat["name"],
                                       "s": sub["name"],
                                       "b": sorted({b["name"] for b in t["brands"]})})
                for b in t["brands"]:
                    for row in b["rows"]:
                        if row and row[0] and row[0] != "-":
                            part_index.append([row[0], u])
    blobs = {}
    for fname, payload in (("search-index.json", prod_index),
                           ("parts-index.json", part_index)):
        blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        (ROOT / "assets" / fname).write_text(blob, encoding="utf-8")
        blobs[fname] = blob

    VER["css"] = digest((ROOT / "assets" / "catalogue.css").read_bytes())
    VER["js"] = digest((ROOT / "assets" / "catalogue-ui.js").read_bytes())
    VER["em"] = digest((ROOT / "assets" / "email-protect.js").read_bytes())
    VER["idx"] = digest(blobs["search-index.json"], blobs["parts-index.json"])

    urls, counts, n_products = ["/"], {}, 0

    for cat in cats:
        # One page per (category, product name). The source data holds a couple
        # of names twice inside one category; those merge into a single page
        # rather than one silently overwriting the other on disk.
        by_name = {}
        for sub in cat["subs"]:
            for t in sub["types"]:
                slot = by_name.setdefault(
                    t["name"], {"sub": sub["name"], "sub_slug": sub["slug"],
                                "groups": []})
                slot["groups"].append((t["cols"], t["brands"]))

        card_brands = {
            n: "|".join(sorted({b["name"] for _, bs in i["groups"] for b in bs}))
            for n, i in by_name.items()}

        types_by_sub = {}
        for name, info in by_name.items():
            rows = sum(len(b["rows"]) for _, bs in info["groups"] for b in bs)
            types_by_sub.setdefault(info["sub"], [info["sub_slug"], []])[1].append(
                (name, f'/products/{cat["slug"]}/{slug(name)}/', rows))
        for v in types_by_sub.values():
            v[1].sort(key=lambda x: x[0])

        for name, info in by_name.items():
            u = f'/products/{cat["slug"]}/{slug(name)}/'
            sibs = [(n, su) for n, su, _ in types_by_sub[info["sub"]][1] if n != name][:14]
            write(OUT / cat["slug"] / slug(name) / "index.html",
                  product_page(cat, info["sub"], name, info["groups"],
                               sibs, u, cats))
            urls.append(u)
            n_products += 1

        cu = f'/products/{cat["slug"]}/'
        counts[cat["slug"]] = (
            len(by_name), sum(r for v in types_by_sub.values() for _, _, r in v[1]))
        write(OUT / cat["slug"] / "index.html",
              category_page(cat, types_by_sub, cu, cats, card_brands))
        urls.append(cu)

    write(OUT / "index.html", hub_page(cats, counts))
    urls.append("/products/")

    # Vercel's static builder serves this automatically for any unmatched
    # path, with a real 404 status. Root-level, not under OUT, and never in
    # the sitemap -- a 404 page has no business being indexed or crawled as
    # a destination.
    write(ROOT / "404.html", not_found_page(cats))

    # Privacy and terms: indexable, listed in the sitemap, and linked from the
    # footer of every page so they are reachable rather than merely present.
    write(ROOT / "privacy" / "index.html", privacy_page(cats))
    urls.append("/privacy/")
    write(ROOT / "terms" / "index.html", terms_page(cats))
    urls.append("/terms/")

    # /industries/ pages are generated separately (build/build.js). The sitemap
    # is rebuilt from scratch here, so they must be listed or they vanish.
    urls.append("/industries/")
    for _seg in [
        "automotive-auto-components",
        "pharmaceutical-life-sciences",
        "food-beverage-agro-processing",
        "engineering-fabrication",
        "textiles-garments",
        "power-utilities-electrical",
        "construction-infrastructure",
        "plastics-packaging-printing"
    ]:
        urls.append(f"/industries/{_seg}/")

    seen, ordered = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)

    def priority(u):
        if u == "/":
            return "1.0"
        return "0.8" if u.count("/") == 3 else "0.6"

    entries = "".join(
        f"\n  <url><loc>{SITE}{u}</loc><changefreq>monthly</changefreq>"
        f"<priority>{priority(u)}</priority></url>" for u in ordered)
    write(ROOT / "sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          f"{entries}\n</urlset>\n")

    print(f"categories : {len(cats)}")
    print(f"products   : {n_products}")
    print(f"sitemap    : {len(ordered)} urls")


if __name__ == "__main__":
    main()
