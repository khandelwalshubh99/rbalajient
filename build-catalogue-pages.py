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
import shutil
from urllib.parse import quote

ROOT = pathlib.Path(__file__).parent
SITE = "https://www.rbalajient.com"
OUT = ROOT / "products"
PHOTOS = ROOT / "assets" / "products"

PHONE = "9302110344"
SALES = "sales@rbalajient.com"
ADDRESS = "118 Siyaganj Main Road, Indore, 452007 (MP)"

# Descriptions the source data failed to resolve — rendering them would put
# "[Category not found]" on a live page.
JUNK_DESC = re.compile(r"^\s*\[.*\]\s*$")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def e(s):
    return html.escape(str(s), quote=True)


def soften(s):
    """Descriptions arrive shouting (C-CLAMP - 55 mm MAX. OPENING). Sentence-case
    the ones that are essentially all-caps; leave mixed-case strings alone."""
    letters = [c for c in s if c.isalpha()]
    if len(letters) > 3 and all(c.isupper() for c in letters):
        return s[0].upper() + s[1:].lower()
    return s


def num(n):
    return f"{n:,}"


def photo_for(name):
    for ext in ("jpg", "png"):
        if (PHOTOS / f"{slug(name)}.{ext}").exists():
            return f"/assets/products/{slug(name)}.{ext}"
    return None


# --------------------------------------------------------------------------
# shared chrome
# --------------------------------------------------------------------------

def head(title, desc, canonical, jsonld):
    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
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
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800;900&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/catalogue.css">
<script type="application/ld+json">{jsonld}</script>
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
        <li><a href="mailto:{SALES}">{SALES}</a></li>
        <li>Mon&ndash;Sat 10:00&ndash;19:30</li>
      </ul>
    </div>
  </div>
  <div class="wrap footer-bar">
    <span>&copy; 2026 Balaji Enterprises. All rights reserved.</span>
    <span>rbalajient.com</span>
  </div>
</footer>
</body>
</html>
"""


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

def product_page(cat, sub, name, groups, lead, sibs, url, cats):
    """groups: [(cols, brands)] — more than one only where the source data holds
    two type entries under the same name in the same category."""
    photo = photo_for(name)
    brands = sorted({b["name"] for _, bs in groups for b in bs})
    n_rows = sum(len(b["rows"]) for _, bs in groups for b in bs)

    meta_desc = (f"{name} — {num(n_rows)} size{'s' if n_rows != 1 else ''} and part "
                 f"numbers from {', '.join(brands[:4])}"
                 f"{' and more' if len(brands) > 4 else ''}, with specifications "
                 f"and list prices. Ready stock from Balaji Enterprises, Indore.")

    crumb_nav, crumb_ld = crumbs([
        ("Home", "/"), ("Products", "/products/"),
        (cat["name"], f'/products/{cat["slug"]}/'), (name, None)])

    prod_ld = {"@type": "Product", "name": name,
               "category": f'{cat["name"]} > {sub}',
               "brand": [{"@type": "Brand", "name": b} for b in brands],
               "url": SITE + url}
    if lead:
        prod_ld["description"] = lead
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

    rel = ""
    if sibs:
        items = "".join(f'<li><a href="{u}">{e(n)}</a></li>' for n, u in sibs)
        rel = f"""
    <section class="related">
      <h2>More in {e(sub)}</h2>
      <ul class="pill-list">{items}</ul>
    </section>"""

    # Percent-encode both, or a product name containing "&" (Abrasive Disc &
    # Paper) truncates the mailto body and leaves a bare & in the attribute.
    subject = quote(f"Quote request: {name}", safe="")
    body = quote(f"Please send current pricing and availability for {name}."
                 "\r\n\r\nSizes / part numbers needed:\r\n", safe="")

    hero = (f'<div class="prod-photo"><img src="{photo}" alt="{e(name)} supplied by '
            f'Balaji Enterprises, Indore" width="300" height="300"></div>'
            if photo else
            '<div class="prod-photo no-photo"><span>Photo on request</span></div>')

    return head(f"{name} — {', '.join(brands[:3])} | Balaji Enterprises Indore",
                meta_desc, SITE + url, ld(prod_ld, crumb_ld)) + f"""
<main id="main">
  <div class="wrap">
    {crumb_nav}
    <div class="prod-head">
      {hero}
      <div class="prod-intro">
        <span class="eyebrow">{e(cat["name"])} &middot; {e(sub)}</span>
        <h1>{e(name)}</h1>
        {f'<p class="lead">{e(lead)}</p>' if lead else ''}
        <p class="meta">{num(n_rows)} listed size{"s" if n_rows != 1 else ""} &amp; part numbers &middot; {len(brands)} brand{"s" if len(brands) != 1 else ""}</p>
        <ul class="brand-chips">{"".join(f"<li>{e(b)}</li>" for b in brands)}</ul>
        <div class="cta-row">
          <a class="btn-primary" href="mailto:{SALES}?subject={subject}&amp;body={body}">Request a Quote</a>
          <a class="btn-outline" href="tel:{PHONE}">Call {PHONE}</a>
        </div>
      </div>
    </div>
    <h2 class="specs-h">Sizes, part numbers &amp; specifications</h2>
    <p class="specs-note">Listed brand by brand. Prices are list prices in INR and
    exclude taxes &mdash; contact us for current trade pricing and availability.</p>
    {"".join(tables)}
    {rel}
  </div>
</main>
""" + footer(cats)


def category_page(cat, types_by_sub, url, cats):
    n_types = sum(len(v) for v in types_by_sub.values())
    n_items = sum(r for v in types_by_sub.values() for _, _, r in v)

    crumb_nav, crumb_ld = crumbs([
        ("Home", "/"), ("Products", "/products/"), (cat["name"], None)])

    listed, blocks, pos = [], [], 0
    for sub, entries in types_by_sub.items():
        cards = []
        for name, u, rows in entries:
            pos += 1
            listed.append({"@type": "ListItem", "position": pos,
                           "name": name, "url": SITE + u})
            ph = photo_for(name)
            thumb = (f'<img src="{ph}" alt="" loading="lazy" width="64" height="64">'
                     if ph else '<span class="thumb-blank" aria-hidden="true"></span>')
            cards.append(f"""
        <li class="type-card"><a href="{u}">{thumb}
          <span class="type-name">{e(name)}</span>
          <span class="type-meta">{num(rows)} size{"s" if rows != 1 else ""}</span></a></li>""")
        blocks.append(f"""
    <section class="sub-block">
      <h2>{e(sub)}</h2>
      <ul class="type-grid">{"".join(cards)}</ul>
    </section>""")

    page_ld = {"@type": "CollectionPage",
               "name": f'{cat["name"]} — Balaji Enterprises',
               "url": SITE + url,
               "mainEntity": {"@type": "ItemList", "numberOfItems": n_types,
                              "itemListElement": listed}}

    desc = (f'{cat["name"]} from Balaji Enterprises, Indore — {n_types} product '
            f"types, {num(n_items)} listed sizes and part numbers with specifications "
            "and list prices. Authorised distributor, ready stock since 1996.")

    return head(f'{cat["name"]} Supplier in Indore | Balaji Enterprises',
                desc, SITE + url, ld(page_ld, crumb_ld)) + f"""
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
    {"".join(blocks)}
  </div>
</main>
""" + footer(cats)


def hub_page(cats, counts, url="/products/"):
    crumb_nav, crumb_ld = crumbs([("Home", "/"), ("Products", None)])
    cards, listed = [], []
    for i, c in enumerate(cats):
        n_types, n_items = counts[c["slug"]]
        listed.append({"@type": "ListItem", "position": i + 1, "name": c["name"],
                       "url": f'{SITE}/products/{c["slug"]}/'})
        cards.append(f"""
      <li class="cat-card"><a href="/products/{c["slug"]}/">
        <span class="cat-n">{i + 1:02d}</span>
        <span class="cat-name">{e(c["name"])}</span>
        <span class="cat-meta">{n_types} product types &middot; {num(n_items)} sizes</span>
        <span class="cat-go">View products &rarr;</span></a></li>""")

    total = sum(v[1] for v in counts.values())
    page_ld = {"@type": "CollectionPage",
               "name": "Product Catalogue — Balaji Enterprises", "url": SITE + url,
               "mainEntity": {"@type": "ItemList", "numberOfItems": len(cats),
                              "itemListElement": listed}}

    return head("Product Catalogue — Industrial Tools & MRO Supplies | Balaji Enterprises",
                f"Browse {num(total)} industrial tool and MRO listings across {len(cats)} "
                "categories — hand tools, power tools, measuring instruments, "
                "abrasives and more, with sizes, part numbers and list prices from "
                "Balaji Enterprises, Indore.",
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
    <ul class="cat-grid">{"".join(cards)}</ul>
  </div>
</main>
""" + footer(cats)


# --------------------------------------------------------------------------

def main():
    raw = (ROOT / "catalogue.js").read_text()
    data = json.loads(raw[raw.index("{"):].rstrip().rstrip(";"))
    cats = data["cats"]

    if OUT.exists():
        shutil.rmtree(OUT)

    urls, counts, n_products = ["/"], {}, 0

    for cat in cats:
        # One page per (category, product name). The source data holds a couple
        # of names twice inside one category; those merge into a single page
        # rather than one silently overwriting the other on disk.
        by_name = {}
        for sub in cat["subs"]:
            for t in sub["types"]:
                slot = by_name.setdefault(
                    t["name"], {"sub": sub["name"], "groups": [], "descs": []})
                slot["groups"].append((t["cols"], t["brands"]))
                d = (t.get("desc") or "").strip()
                if d and not JUNK_DESC.match(d):
                    slot["descs"].append(d)

        types_by_sub = {}
        for name, info in by_name.items():
            rows = sum(len(b["rows"]) for _, bs in info["groups"] for b in bs)
            types_by_sub.setdefault(info["sub"], []).append(
                (name, f'/products/{cat["slug"]}/{slug(name)}/', rows))
        for v in types_by_sub.values():
            v.sort(key=lambda x: x[0])

        for name, info in by_name.items():
            u = f'/products/{cat["slug"]}/{slug(name)}/'
            sibs = [(n, su) for n, su, _ in types_by_sub[info["sub"]] if n != name][:14]
            lead = soften(info["descs"][0]) if info["descs"] else ""
            write(OUT / cat["slug"] / slug(name) / "index.html",
                  product_page(cat, info["sub"], name, info["groups"], lead,
                               sibs, u, cats))
            urls.append(u)
            n_products += 1

        cu = f'/products/{cat["slug"]}/'
        counts[cat["slug"]] = (
            len(by_name), sum(r for v in types_by_sub.values() for _, _, r in v))
        write(OUT / cat["slug"] / "index.html",
              category_page(cat, types_by_sub, cu, cats))
        urls.append(cu)

    write(OUT / "index.html", hub_page(cats, counts))
    urls.append("/products/")

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
