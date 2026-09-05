#!/usr/bin/env python3
"""Build the Aspen Bear Week static site.

Real multi-page output, because search engines do not index hash fragments as
separate pages and the knowledge layer is the SEO surface. One source of truth
for the nav and footer so six pages cannot drift apart.

Paths are relative throughout so the site works both at a GitHub Pages project
subpath and at the root of a custom domain, with no rebuild in between.
"""
import os, re, html, shutil

OUT = "abw-repo"
# Swap to https://aspenbearweek.org once the domain is live and the CNAME is set.
SITE_URL = "https://connor396.github.io/aspen-bear-week"

PAGES = [
    dict(slug="",             nav="Home",         title="Aspen Bear Week",
         desc="Colorado is having its worst bear year on record. Aspen Bear Week restores the native forage bears lost to drought, far from town. Habitat restoration, not feeding."),
    dict(slug="the-work",     nav="The Work",     title="The Work",
         desc="How Aspen Bear Week restores native bear forage: parcel analysis to find the ground, replanting Gambel oak, serviceberry and chokecherry, and Bear Aware education."),
    dict(slug="bear-aware",   nav="Bear Aware",   title="Bear Aware",
         desc="Why there are so many bears in Aspen this year, what to do if you see one, the Aspen and Pitkin County trash rules, and why habitat restoration is not feeding."),
    dict(slug="bear-week",    nav="Bear Week",    title="Bear Week",
         desc="A town-wide week funding bear habitat restoration in Aspen. How local businesses become founding partners and display the Proud Partner decal."),
    dict(slug="about",        nav="About",        title="About",
         desc="Where Aspen Bear Week actually stands: entity status, donations, board, and our first measurable target. Specific about what is real and what is not."),
    dict(slug="get-involved", nav="Get Involved", title="Get Involved",
         desc="Most of what Aspen Bear Week needs right now is not money: land, founding business partners, volunteers, and residents securing their own attractants."),
]
NAV = [p for p in PAGES if p["slug"] not in ("", "get-involved")]


def rel(slug):
    """Prefix from a page back to the site root."""
    return "" if slug == "" else "../"


def head(p):
    r = rel(p["slug"])
    canonical = SITE_URL + ("/" if p["slug"] == "" else f"/{p['slug']}/")
    full_title = p["title"] if p["slug"] == "" else f"{p['title']} · Aspen Bear Week"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(p['desc'])}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Aspen Bear Week">
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(p['desc'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/assets/img/grove.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F2A900">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{r}assets/css/site.css">
</head>
<body>
"""


def nav(current):
    r = rel(current)
    items = "".join(
        f'<a href="{r}{p["slug"]}/"{" aria-current=\"page\"" if p["slug"] == current else ""}>{p["nav"]}</a>'
        for p in NAV
    )
    return f"""<nav class="nav">
  <div class="nav-in">
    <a class="brand" href="{r}">Aspen Bear Week<small>Aspen, Colorado</small></a>
    <button class="burger" id="burger" aria-expanded="false" aria-controls="links">Menu</button>
    <div class="links" id="links">{items}</div>
    <a class="cta" href="{r}get-involved/"><span class="cta-long">Get Involved</span><span class="cta-short">Join</span></a>
  </div>
</nav>
"""


FOOT = """<footer>
  <div class="wrap foot">
    <div>
      <span class="eyebrow">Aspen Bear Week &middot; Aspen, Colorado</span>
      <p>An organisation in formation. Nothing on this site is a solicitation for donations, and
         no charitable status is claimed. Photographs are illustrative and are not documentation
         of specific sites, animals or events.</p>
    </div>
    <div>
      <span class="eyebrow">Figures</span>
      <p>Bear activity data from Colorado Parks and Wildlife reporting, 2026. Legal references:
         C.R.S. 33-6-131 and HB26-1342.</p>
    </div>
  </div>
</footer>
<script>
(function(){
  var b = document.getElementById("burger"), l = document.getElementById("links");
  if (!b || !l) return;
  b.addEventListener("click", function(){
    var open = l.classList.toggle("open");
    b.setAttribute("aria-expanded", open ? "true" : "false");
  });
})();
</script>
</body>
</html>
"""

ORG_LD = """<script type="application/ld+json">
{"@context":"https://schema.org","@type":"NGO","name":"Aspen Bear Week",
 "url":"%(u)s/","description":"Restoring native bear forage habitat around Aspen, Colorado.",
 "areaServed":{"@type":"Place","name":"Aspen, Pitkin County, Colorado"},
 "image":"%(u)s/assets/img/grove.jpg"}
</script>
""" % {"u": SITE_URL}


def build_bodies():
    """Page bodies. Content is carried over verbatim from the reviewed build."""
    src = open("abw-site.html", encoding="utf-8").read()
    bodies = {}
    for vid, slug in [("v-home",""),("v-work","the-work"),("v-aware","bear-aware"),
                      ("v-week","bear-week"),("v-about","about"),("v-involved","get-involved")]:
        m = re.search(r'<div class="view" id="%s">(.*?)\n</div>\n' % vid, src, re.S)
        if not m:
            raise SystemExit(f"could not extract {vid}")
        body = m.group(1)
        # rewrite in-page hash routes to real page URLs
        r = rel(slug)
        body = body.replace('href="#/involved"', f'href="{r}get-involved/"')
        body = body.replace('href="#/work"',     f'href="{r}the-work/"')
        body = body.replace('href="#/aware"',    f'href="{r}bear-aware/"')
        body = body.replace('href="#/week"',     f'href="{r}bear-week/"')
        body = body.replace('href="#/about"',    f'href="{r}about/"')
        body = body.replace('href="#/"',         f'href="{r}"')
        # data-URI placeholders become real asset files
        for token, name in [("{{IMG_GROVE}}","grove"),("{{IMG_SCRUB}}","scrub"),
                            ("{{IMG_BEAR}}","bear"),("{{IMG_VALLEY}}","valley")]:
            body = body.replace(token, f"{r}assets/img/{name}.jpg")
        body = body.replace("<img ", '<img loading="lazy" decoding="async" ')
        bodies[slug] = body
    return bodies


def main():
    bodies = build_bodies()
    for p in PAGES:
        slug = p["slug"]
        d = OUT if slug == "" else os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        extra = ORG_LD if slug == "" else ""
        doc = head(p) + nav(slug) + bodies[slug] + extra + FOOT
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(doc)
        print("wrote", os.path.join(d, "index.html"))

    urls = "".join(
        f"  <url><loc>{SITE_URL}{'/' if p['slug']=='' else '/'+p['slug']+'/'}</loc>"
        f"<changefreq>weekly</changefreq><priority>{'1.0' if p['slug']=='' else '0.8'}</priority></url>\n"
        for p in PAGES)
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")

    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")

    open(os.path.join(OUT, ".nojekyll"), "w").write("")

    nf = head(dict(slug="", title="Page not found", desc="That page does not exist.")) \
         + nav("") + """
<section class="band-gold" style="border-bottom:3px solid var(--ink)">
  <div class="wrap"><span class="eyebrow">404</span>
  <h2>That page does not exist.</h2>
  <div class="btns"><a class="btn" href="/">Back to the start</a></div></div>
</section>
""" + FOOT
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(nf)

    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(
        "# Aspen Bear Week\n\n"
        "Static site for Aspen Bear Week, a habitat-restoration effort in Aspen, Colorado.\n\n"
        "## Build\n\n"
        "Pages are generated by `build.py` from a single nav/footer source so they cannot drift.\n"
        "Output is plain HTML and CSS: **no dependencies, no build step at deploy time, no server,\n"
        "no database.** GitHub Pages serves the repo as-is.\n\n"
        "## Security posture\n\n"
        "This site never handles money, credentials or personal data. Donations, when they open,\n"
        "run through an established third-party platform and are linked, never embedded as a form\n"
        "we wrote. There are no accounts, no login, no admin route and no secrets in this repo.\n\n"
        "## Custom domain\n\n"
        "Set `SITE_URL` in `build.py`, add a `CNAME` file containing the domain, point DNS at\n"
        "GitHub Pages, then rebuild.\n\n"
        "## Images\n\n"
        "Photographs are illustrative and are captioned as such. They are not documentation of\n"
        "specific sites, animals or events in Aspen.\n")

    print("\nsitemap, robots.txt, 404, .nojekyll, README written")


if __name__ == "__main__":
    main()
