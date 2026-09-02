#!/usr/bin/env python3
"""Generate the deployable index.html from the Claude Design source.

Keeps 'Balaji Enterprises.dc.html' untouched as the editable design source; the
live page differs from it in exactly three ways:
  1. a real <head> (title / description / favicon / lang)
  2. the image-slot authoring widget swapped for a neutral placeholder
  3. no dependency on image-slot.js
"""
import sys, pathlib, re

src = pathlib.Path(sys.argv[1]).read_text()
out = pathlib.Path(sys.argv[2])

def sub(old, new, label):
    global src
    if old not in src:
        sys.exit("FAILED to find anchor: " + label)
    src = src.replace(old, new, 1)

# --- 1. head -------------------------------------------------------------
SITE  = "https://www.rbalajient.com/"
TITLE = "Balaji Enterprises — Industrial Tools &amp; MRO Supplier in Indore"
DESC  = ("Authorised distributor of hand tools, power tools, measuring instruments and "
         "industrial MRO equipment in Indore, Madhya Pradesh. 12,000+ items across 25 "
         "leading brands, ready stock since 1996.")

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
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "118 Siyaganj Main Road",
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
<script src="./support.js"></script>
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
<script src="./support.js"></script>
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

sub('<script src="./catalogue.js"></script>',
    '<script src="./catalogue.js" defer></script>', "catalogue.js defer")

out.write_text(src)
print("wrote", out, len(src), "bytes")
