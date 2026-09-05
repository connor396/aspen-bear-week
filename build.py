#!/usr/bin/env python3
"""Build the Aspen Bear Week static site.

Real multi-page output, because search engines do not index hash fragments as
separate pages and the knowledge layer is the SEO surface. One source of truth
for the nav and footer so six pages cannot drift apart.

Paths are relative throughout so the site works both at a GitHub Pages project
subpath and at the root of a custom domain, with no rebuild in between.
"""
import os, re, html, shutil

OUT = "."
# Swap to https://aspenbearweek.org once the domain is live and the CNAME is set.
SITE_URL = "https://connor396.github.io/aspen-bear-week"

# The email platform's form endpoint. The list lives there, never here: this repo
# holds no handler, no datastore and no secret. See ~/.claude/context/anatomy/cause-site.md.
# While this is empty every capture renders as an explanation with no input, so nothing
# broken ever ships. Setting it is the single change that puts capture live.
FORM_ACTION = ""
FORM_EMAIL_FIELD = "email"   # platform's field name for the address
FORM_TAG_FIELD = "source"    # hidden field recording which surface the signup came from

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
    dict(slug="privacy",      nav="Privacy",      title="Privacy",
         desc="What Aspen Bear Week collects, why, who processes it, and how to leave the list. We hold no payment details and run no accounts."),
]
NAV = [p for p in PAGES if p["slug"] not in ("", "get-involved", "privacy")]


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


FOOT_TPL = """<section class="band-ink signup-band">
  <div class="wrap">
    <div class="signup-grid">
      <div>
        <h2 class="signup-h">Nothing happens here without people who live here.</h2>
        <p class="signup-p">Where the ground is, when the planting days are, and what the
          state decides next. Sent when there is something to say and not otherwise.</p>
      </div>
      {SIGNUP}
    </div>
  </div>
</section>
<footer>
  <div class="wrap foot">
    <div>
      <span class="eyebrow">Aspen Bear Week &middot; Aspen, Colorado</span>
      <p>An organisation in formation. Nothing on this site is a solicitation for donations, and
         no charitable status is claimed. Photographs are illustrative and are not documentation
         of specific sites, animals or events.</p>
      <nav class="foot-links" aria-label="Footer">
        <a href="{R}privacy/">Privacy</a>
        <a href="{R}get-involved/">Get involved</a>
        <a href="{R}about/">Where this stands</a>
      </nav>
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


def foot(slug):
    r = rel(slug)
    block = signup("footer", "Get the field notes",
                   cta="Join the list", quiet=True).replace("{R}", r)
    out = FOOT_TPL.replace("{SIGNUP}", block).replace("{R}", r)
    if not block:
        # drop the band wholesale rather than leave a heading over an empty column
        i, j = out.index('<section class="band-ink signup-band">'), out.index("<footer>")
        out = out[:i] + out[j:]
    return out

ORG_LD = """<script type="application/ld+json">
{"@context":"https://schema.org","@type":"NGO","name":"Aspen Bear Week",
 "url":"%(u)s/","description":"Restoring native bear forage habitat around Aspen, Colorado.",
 "areaServed":{"@type":"Place","name":"Aspen, Pitkin County, Colorado"},
 "image":"%(u)s/assets/img/grove.jpg"}
</script>
""" % {"u": SITE_URL}



# ============================================================================
# Capture. One component, three placements. The list lives in the email
# platform; this repo only draws the line people write on.
# ============================================================================

def signup(source, label, cta="Join the list", note="", choices=None, quiet=False):
    """A ledger line, not a card.

    With FORM_ACTION unset the input is omitted entirely rather than rendered
    dead, so a half-built capture can never reach the live site.
    """
    note_html = f'<p class="cap-note">{note}</p>' if note else ""
    if choices:
        opts = "".join(f'<option value="{v}">{t}</option>' for v, t in choices)
        tag_field = (f'<select class="cap-select" name="{FORM_TAG_FIELD}" '
                     f'aria-label="What brings you here">{opts}</select>')
    else:
        tag_field = f'<input type="hidden" name="{FORM_TAG_FIELD}" value="{source}">' 
    if not FORM_ACTION:
        if quiet:
            return ""
        return f'''<div class="capture">
  <label class="cap-label">{label}</label>
  <p class="cap-pending">The list opens with the domain, this week. Until then reach the
     organisers directly.</p>
  {note_html}
</div>'''
    return f'''<div class="capture">
  <form class="cap-form" action="{FORM_ACTION}" method="post">
    <label class="cap-label" for="e-{source}">{label}</label>
    <div class="cap-row">
      <input class="cap-input" id="e-{source}" type="email" name="{FORM_EMAIL_FIELD}"
             required autocomplete="email" placeholder="you@example.com"
             aria-describedby="n-{source}">
      {tag_field}
      <button class="btn cap-btn" type="submit">{cta}</button>
    </div>
    <p class="cap-note" id="n-{source}">One email a month at most. Leave whenever you like.
       <a href="{{R}}privacy/">What we collect</a>.</p>
  </form>
  {note_html}
</div>'''


def build_bodies():
    """Page bodies. Content is carried over verbatim from the reviewed build."""
    src = open("src/content.html", encoding="utf-8").read()
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
    bodies["get-involved"] = body_involved(rel("get-involved"))
    bodies["privacy"] = body_privacy(rel("privacy"))
    return bodies



# ============================================================================
# Pages written here rather than extracted, because they carry the capture
# component and did not exist in the reviewed single-file source.
# ============================================================================

GATE = [
    ("Confirm the charity is alive",
     "The exact legal name and EIN, checked current in the IRS Tax Exempt Organization "
     "Search and with the Colorado Secretary of State. An entity that was formed and never "
     "filed can lose its exempt status without anyone being told."),
    ("Open an account the organisation controls",
     "Not a founder's account, not a sponsor's. The board's."),
    ("Register to fundraise in Colorado",
     "Colorado requires a charity to register with the Secretary of State before it asks "
     "anyone in the state for money. That is the law whatever the cause."),
    ("Turn on a payment platform that carries its own compliance",
     "Card details get handled by a company whose entire business is handling card details. "
     "We will never build that ourselves and we will never hold your card."),
]


def body_involved(r):
    gate = "".join(
        '<li class="gate-item"><h3>%s</h3><p>%s</p></li>' % (t, d) for t, d in GATE)
    cap = signup("involved", "Where should we put you?",
                 cta="Put me on the list",
                 choices=[("resident", "I live here"),
                          ("business", "I run a business here"),
                          ("land", "I own or manage land"),
                          ("volunteer", "I want to plant or teach"),
                          ("visitor", "I am visiting Aspen")]).replace("{R}", r)
    fund = signup("fund", "Tell me when the fund opens",
                  cta="Tell me then", quiet=True).replace("{R}", r)
    return """
<section class="band-gold" style="border-bottom:3px solid var(--ink)">
  <div class="wrap">
    <span class="eyebrow">Get involved</span>
    <h2>Most of what we need right now is not money.</h2>
    <p class="lede" style="color:var(--ink);opacity:.85">Four things move this forward this
      month, and only one of them costs anything. Donations are not open yet, and further
      down we show you exactly why.</p>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="paths">
      <article class="path path-lead">
        <span class="eyebrow">If you own or manage land</span>
        <h3>Talk to us about a site</h3>
        <p>Ground in the right place, well away from housing, is the single thing standing
          between this and a first planting season. Private land moves fastest because it
          answers to one owner rather than to a federal calendar.</p>
        <p>A first conversation commits you to nothing and costs an hour. We would rather
          hear no from ten owners than keep guessing at where the ground is.</p>
      </article>
      <article class="path path-lead">
        <span class="eyebrow">If you run a business here</span>
        <h3>Become a founding partner</h3>
        <p>Display the decal, join the directory, and hand every visitor who asks about
          bears a straight answer instead of a shrug. Founding partners are listed by name
          for as long as this runs.</p>
        <p>No fee in the first year. We are asking for your window and for your staff to
          know the answer, not for your money.</p>
      </article>
      <article class="path">
        <span class="eyebrow">If you have time</span>
        <h3>Plant, or teach</h3>
        <p>Planting days need hands and knees. Education needs people who can talk to a
          visitor about bears without lecturing them, which is rarer.</p>
      </article>
      <article class="path">
        <span class="eyebrow">If you live here</span>
        <h3>Secure your own attractants</h3>
        <p>Lock the bin, take down the feeder, pick the fruit before it drops. Unglamorous,
          free, and the highest-return thing any resident does all year.</p>
      </article>
    </div>
    %s
  </div>
</section>

<section class="band-ink">
  <div class="wrap">
    <span class="eyebrow">The restoration fund</span>
    <h2>We are not taking donations, and here is the list we have to finish first.</h2>
    <p class="lede">Most new causes put up a donate button and work this out afterwards. Four
      things have to be true before anyone can responsibly take a dollar, and right now none
      of them is. When they are all done this page will say so, with dates.</p>
    <ol class="gate">%s</ol>
    <p class="gate-foot">Until every one of those is finished there is no donate button on
      this site and no amount you can type anywhere on it. If someone asks you for money in
      this organisation's name today, it is not us.</p>
    %s
  </div>
</section>
""" % (cap, gate, fund)


def body_privacy(r):
    return """
<section class="band-gold" style="border-bottom:3px solid var(--ink)">
  <div class="wrap">
    <span class="eyebrow">Privacy</span>
    <h2>We collect an email address, and only if you type one.</h2>
    <p class="lede" style="color:var(--ink);opacity:.85">This page is short because there is
      very little to describe. Last reviewed 5 September 2026.</p>
  </div>
</section>

<section>
  <div class="wrap">
    <dl class="facts">
      <div class="fact"><dt>What we collect</dt>
        <dd>Your email address, and which part of the site you signed up from, so that land
          questions go to the people who mentioned land. Nothing else. There is no name
          field, no phone field and no address field anywhere on this site.</dd></div>
      <div class="fact"><dt>What we never collect</dt>
        <dd>Payment details. This site has no donation form and no shop, so there is no card
          number here to lose. There are no accounts and no passwords either.</dd></div>
      <div class="fact"><dt>Who else sees it</dt>
        <dd>The list is held by our email provider, who processes it on our behalf and does
          not sell it. We keep no separate copy and this website itself stores nothing.</dd></div>
      <div class="fact"><dt>Cookies</dt>
        <dd>None. No analytics, no advertising pixels, no third-party trackers. That is why
          you have not been asked to accept anything.</dd></div>
      <div class="fact"><dt>How often we write</dt>
        <dd>At most monthly, and only when something has actually happened.</dd></div>
      <div class="fact"><dt>Leaving</dt>
        <dd>Every email carries an unsubscribe link that works immediately. You can also ask
          us to delete your address outright and we will, without asking why.</dd></div>
      <div class="fact"><dt>Children</dt>
        <dd>This is not aimed at children and we do not knowingly hold a child's address.</dd></div>
      <div class="fact"><dt>Reaching a person</dt>
        <dd>Until the organisation's own address is live, reach the organisers directly. This
          line will carry an address as soon as there is one worth publishing.</dd></div>
    </dl>
    <p class="cap-note" style="margin-top:26px">If this page and what the site actually does
      ever disagree, the page is the thing that is wrong, and we want to know.</p>
  </div>
</section>
"""


def main():
    bodies = build_bodies()
    for p in PAGES:
        slug = p["slug"]
        d = OUT if slug == "" else os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        extra = ORG_LD if slug == "" else ""
        doc = head(p) + nav(slug) + bodies[slug] + extra + foot(slug)
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
""" + foot("")
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(nf)

    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(
        "# Aspen Bear Week\n\n"
        "Static site for Aspen Bear Week, a habitat-restoration effort in Aspen, Colorado.\n\n"
        "## Build\n\n"
        "Pages are generated by `build.py` from a single nav/footer source so they cannot drift.\n"
        "Output is plain HTML and CSS: **no dependencies, no build step at deploy time, no server,\n"
        "no database.** GitHub Pages serves the repo as-is.\n\n"
        "## Security posture\n\n"
        "This site handles no money and no credentials. It has no accounts, no login, no admin\n"
        "route, no server, no database and no secrets in the repo.\n\n"
        "**Email capture posts straight to a hosted email platform.** The list is stored there,\n"
        "never here: this repo contains no form handler and nothing that writes to disk. Consent,\n"
        "unsubscribes and suppression are the platform's job because they are compliance surface.\n"
        "Set `FORM_ACTION` in `build.py` to the platform endpoint. While it is empty every capture\n"
        "renders as an explanation with no input, so a half-wired form cannot reach the live site.\n\n"
        "**Donations, when they open, run through a hosted nonprofit platform, linked and never\n"
        "embedded as a form we wrote.** Four things gate that and they are listed on /get-involved/:\n"
        "confirmed 501(c)(3) status, an account the organisation controls, Colorado charitable\n"
        "solicitation registration, and platform onboarding. Until all four clear, this site\n"
        "carries no donate button and no amount field anywhere. That is a legal requirement, not\n"
        "a style choice.\n\n"
        "## Custom domain\n\n"
        "Set `SITE_URL` in `build.py`, add a `CNAME` file containing the domain, point DNS at\n"
        "GitHub Pages, then rebuild.\n\n"
        "## Images\n\n"
        "Photographs are illustrative and are captioned as such. They are not documentation of\n"
        "specific sites, animals or events in Aspen.\n")

    print("\nsitemap, robots.txt, 404, .nojekyll, README written")


if __name__ == "__main__":
    main()
