"""Verify the Aspen Bear Week build at phone and tablet widths.

Checks the things that actually break: horizontal overflow, touch target size,
and whether the new capture components render where they should.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8899"
ROUTES = ["/", "/get-involved/", "/privacy/", "/bear-aware/", "/about/"]
WIDTHS = [(375, 812, "phone"), (768, 1024, "tablet"), (1280, 900, "desktop")]
OUT = r"C:\Users\cknel\AppData\Local\Temp\claude\C--Users-cknel\cc367843-128d-4bbe-aede-af80c16edeed\scratchpad"

fails = []

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for w, h, label in WIDTHS:
        page = b.new_page(viewport={"width": w, "height": h})
        for r in ROUTES:
            page.goto(BASE + r, wait_until="networkidle")

            # 1. horizontal overflow
            sw = page.evaluate("document.documentElement.scrollWidth")
            if sw > w + 1:
                # name the widest offender so the fix is actionable
                who = page.evaluate("""() => {
                  let worst = null, max = 0;
                  document.querySelectorAll('*').forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.right > max) { max = r.right; worst = el; }
                  });
                  return worst ? worst.tagName + '.' + (worst.className || '') +
                                 ' right=' + Math.round(max) : 'unknown';
                }""")
                fails.append(f"OVERFLOW {label} {r}: scrollWidth {sw} > {w}  <- {who}")

            # 2. touch targets on interactive elements
            small = page.evaluate("""() => {
              const out = [];
              document.querySelectorAll('a,button,input,select').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width === 0 && r.height === 0) return;      // hidden
                // WCAG 2.5.8 exempts links inline in a sentence: boxing one to
                // 44px breaks the line it sits in. Controls are still checked.
                const p = el.parentElement;
                if (el.tagName === 'A' && p && p.tagName === 'P' &&
                    p.textContent.trim().length > el.textContent.trim().length + 12) return;
                if (r.height < 44) out.push(
                  (el.tagName + '.' + (el.className||'')).slice(0,50)
                  + ' h=' + Math.round(r.height));
              });
              return [...new Set(out)];
            }""")
            if small and label == "phone":
                fails.append(f"TOUCH {label} {r}: " + "; ".join(small[:6]))

        page.close()

    # 3. capture components. Two states are valid and the build picks one from
    #    FORM_ACTION, so assert against whichever shipped rather than assuming.
    page = b.new_page(viewport={"width": 375, "height": 812})
    page.goto(BASE + "/get-involved/", wait_until="networkidle")
    live = page.locator(".cap-form").count() > 0
    state = "live" if live else "pending"

    if live:
        if page.locator(".cap-form").count() != 3:
            fails.append("CAPTURE live: get-involved should carry 3 forms "
                         f"(found {page.locator('.cap-form').count()})")
        page.goto(BASE + "/", wait_until="networkidle")
        if page.locator(".signup-band .cap-form").count() != 1:
            fails.append("CAPTURE live: sitewide signup band missing on home")
    else:
        # exactly one honest notice on the page about getting involved, and no
        # empty signup band stranded in any footer
        if page.locator(".cap-pending").count() != 1:
            fails.append("CAPTURE pending: get-involved should carry exactly one "
                         f"notice (found {page.locator('.cap-pending').count()})")
        for r in ROUTES:
            page.goto(BASE + r, wait_until="networkidle")
            if page.locator(".signup-band").count():
                fails.append(f"CAPTURE pending: empty signup band left on {r}")

    page.goto(BASE + "/get-involved/", wait_until="networkidle")
    if page.locator(".gate-item").count() != 4:
        fails.append("GATE: expected 4 gate items")

    # 4. E3, no solicitation controls anywhere
    for r in ROUTES:
        page.goto(BASE + r, wait_until="networkidle")
        bad = page.evaluate("""() => {
          const out = [];
          document.querySelectorAll('input,button,a').forEach(el => {
            const t = (el.textContent||'') + ' ' + (el.name||'') + ' ' + (el.type||'');
            if (/\\bdonate now\\b|\\bgive now\\b|amount/i.test(t)) out.push(t.trim().slice(0,40));
          });
          return out;
        }""")
        if bad:
            fails.append(f"SOLICITATION {r}: {bad}")

    # screenshots for the record
    for w, h, label in [(375, 812, "phone"), (768, 1024, "tablet")]:
        p2 = b.new_page(viewport={"width": w, "height": h})
        for name, route in [("involved", "/get-involved/"), ("home", "/")]:
            p2.goto(BASE + route, wait_until="networkidle")
            p2.screenshot(path=f"{OUT}/v-{name}-{label}.png", full_page=True)
        p2.close()

    b.close()

print("=" * 60)
if fails:
    print("FAIL")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print(f"PASS [{state} capture state]: no overflow, touch targets >=44px, "
      "captures correct for the state, no solicitation controls")
