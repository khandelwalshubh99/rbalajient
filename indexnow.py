#!/usr/bin/env python3
"""Submit every sitemap URL to IndexNow.

Bing, Yandex, Seznam and Naver share one IndexNow endpoint: a submission asks
them to recrawl now instead of waiting for a schedule that, on this domain, has
not come round since the site first went up. Google does not participate, so
Search Console stays the route there.

Ownership is proved by serving the key back from the site root, which means the
deploy carrying f65d0ad1e9ddde865e64f64a8f763bf1.txt has to be live *before*
this runs. The check below refuses to submit until it is.

  python3 indexnow.py             # submit every URL in sitemap.xml
  python3 indexnow.py --dry-run   # show what would be sent, send nothing
"""
import json, pathlib, sys, urllib.error, urllib.request
import xml.etree.ElementTree as ET

HOST = "www.rbalajient.com"
KEY = "f65d0ad1e9ddde865e64f64a8f763bf1"
KEY_URL = "https://%s/%s.txt" % (HOST, KEY)
ENDPOINT = "https://api.indexnow.org/indexnow"
UA = "rbalajient-indexnow/1.0"

# Documented response codes, so a failure says what to do rather than a number.
MEANING = {
    400: "bad request: the JSON payload was rejected",
    403: "key not valid: %s did not serve the key. Has the deploy gone live?" % KEY_URL,
    422: "a URL does not belong to %s, or the key does not match the host" % HOST,
    429: "too many requests: submitting the same URLs too often. Try again later.",
}

dry_run = "--dry-run" in sys.argv

here = pathlib.Path(__file__).parent
local_key = here / (KEY + ".txt")
if not local_key.exists():
    sys.exit("missing %s: the key file has to sit at the site root" % local_key.name)
if local_key.read_text().strip() != KEY:
    sys.exit("%s does not contain the key this script submits" % local_key.name)

urls = [loc.text.strip() for loc in ET.parse(here / "sitemap.xml").getroot().iter(
    "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
if not urls:
    sys.exit("sitemap.xml lists no URLs")
off_host = [u for u in urls if not u.startswith("https://%s/" % HOST)]
if off_host:
    sys.exit("sitemap URL is not on %s: %s" % (HOST, off_host[0]))

print("%d URLs from sitemap.xml, key at %s" % (len(urls), KEY_URL))

if dry_run:
    for u in urls[:5]:
        print("  " + u)
    print("  ... and %d more" % (len(urls) - 5))
    print("dry run: nothing submitted")
    sys.exit(0)

# The endpoint fetches the key itself, but its 403 does not say which half is
# wrong. Checking first turns "deploy has not landed yet" into a clear message.
try:
    with urllib.request.urlopen(
            urllib.request.Request(KEY_URL, headers={"User-Agent": UA}), timeout=20) as r:
        if r.read().decode().strip() != KEY:
            sys.exit("%s is live but serves something else" % KEY_URL)
except urllib.error.HTTPError as e:
    sys.exit("%s returned HTTP %d. Deploy the key file before submitting." % (KEY_URL, e.code))
except urllib.error.URLError as e:
    sys.exit("could not reach %s (%s)" % (KEY_URL, e.reason))

body = json.dumps({
    "host": HOST,
    "key": KEY,
    "keyLocation": KEY_URL,
    "urlList": urls,
}).encode()

req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": UA,
})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("HTTP %d: %d URLs accepted" % (r.status, len(urls)))
except urllib.error.HTTPError as e:
    sys.exit("HTTP %d: %s" % (e.code, MEANING.get(e.code, e.read().decode()[:200])))
except urllib.error.URLError as e:
    sys.exit("could not reach %s (%s)" % (ENDPOINT, e.reason))
