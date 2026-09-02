#!/usr/bin/env python3
"""Generate the deployable index.html from the Claude Design source.

Keeps 'Balaji Enterprises.dc.html' untouched as the editable design source; the
live page differs from it in exactly three ways:
  1. a real <head> (title / description / favicon / lang)
  2. the image-slot authoring widget swapped for a neutral placeholder
  3. no dependency on image-slot.js
"""
import sys, pathlib

src = pathlib.Path(sys.argv[1]).read_text()
out = pathlib.Path(sys.argv[2])

def sub(old, new, label):
    global src
    if old not in src:
        sys.exit("FAILED to find anchor: " + label)
    src = src.replace(old, new, 1)

# --- 1. head -------------------------------------------------------------
sub(
'''<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="./support.js"></script>
</head>''',
'''<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Balaji Enterprises — Tools &amp; Industrial Supply</title>
<meta name="description" content="Balaji Enterprises supplies hand tools, power tools and industrial MRO equipment to manufacturers, dealers and businesses across Madhya Pradesh. Authorised distributor for 20+ leading brands since 1996.">
<link rel="icon" href="assets/logo.png" type="image/png">
<link rel="canonical" href="https://www.rbalajient.com/">
<meta property="og:type" content="website">
<meta property="og:title" content="Balaji Enterprises — Tools &amp; Industrial Supply">
<meta property="og:description" content="Hand tools, power tools and industrial MRO equipment across Madhya Pradesh. Authorised distributor since 1996.">
<meta property="og:image" content="https://www.rbalajient.com/assets/logo.png">
<meta property="og:url" content="https://www.rbalajient.com/">
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

out.write_text(src)
print("wrote", out, len(src), "bytes")
