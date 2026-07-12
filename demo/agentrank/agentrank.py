#!/usr/bin/env python3
"""Agentrank — agent-readiness auditor for Shopify storefronts.

Answers one question: when an AI shopping agent (ChatGPT, Google, Copilot)
tries to read, rank, and buy from this store, what does it actually see?

Runs ~23 concrete checks against a live store's public surface — catalog
feed, robots directives for AI crawlers, JSON-LD structured data, variant
clarity, policy pages — and renders a scored HTML report, optionally
side-by-side with a competitor.

Zero dependencies (stdlib only).

Usage:
    python3 agentrank.py https://yourstore.com -o report.html
    python3 agentrank.py https://yourstore.com --compare https://rival.com -o report.html
    python3 agentrank.py --fixture fixtures/driftwood --compare fixtures/hearthline -o report.html
"""

import argparse
import datetime
import html as html_mod
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

AI_AGENTS = [
    ("GPTBot", "OpenAI · training + retrieval"),
    ("OAI-SearchBot", "OpenAI · ChatGPT shopping/search"),
    ("ChatGPT-User", "OpenAI · live user browsing"),
    ("ClaudeBot", "Anthropic · Claude"),
    ("Google-Extended", "Google · Gemini grounding"),
    ("PerplexityBot", "Perplexity"),
    ("Bingbot", "Microsoft · Copilot"),
]

UA = "AgentrankAudit/0.1 (agent-readiness check; contact site owner ran this)"


# --------------------------------------------------------------------------- #
# Sources: where audit bytes come from (live site or recorded fixture)
# --------------------------------------------------------------------------- #

class LiveSource:
    def __init__(self, base_url):
        if not base_url.startswith("http"):
            base_url = "https://" + base_url
        p = urllib.parse.urlparse(base_url)
        self.base = f"{p.scheme}://{p.netloc}"
        self.name = p.netloc.replace("www.", "")
        self.url = p.netloc
        self.timings = []

    def get(self, path):
        req = urllib.request.Request(self.base + path, headers={"User-Agent": UA})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read(2_500_000).decode("utf-8", "replace")
                self.timings.append(time.time() - t0)
                return r.status, body
        except urllib.error.HTTPError as e:
            self.timings.append(time.time() - t0)
            return e.code, ""
        except Exception:
            self.timings.append(time.time() - t0)
            return 0, ""


class FixtureSource:
    """Replays a recorded store surface from a directory of files."""

    FILES = {
        "/": "home.html",
        "/robots.txt": "robots.txt",
        "/llms.txt": "llms.txt",
        "/sitemap.xml": "sitemap.xml",
        "/products.json": "products.json",
        "/policies/shipping-policy": "shipping-policy.html",
        "/policies/refund-policy": "refund-policy.html",
        "/pages/contact": "contact.html",
    }

    def __init__(self, dirpath):
        self.dir = dirpath
        meta = json.load(open(os.path.join(dirpath, "store.json")))
        self.name = meta["name"]
        self.url = meta["url"]
        self.timings = [0.4]

    def get(self, path):
        clean = path.split("?")[0]
        fname = self.FILES.get(clean)
        if fname is None and clean.startswith("/products/"):
            fname = "product.html"
        if fname is None:
            return 404, ""
        fp = os.path.join(self.dir, fname)
        if not os.path.exists(fp):
            return 404, ""
        return 200, open(fp, encoding="utf-8").read()


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #

def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html_mod.unescape(s)).strip()


def extract_jsonld(page):
    """All JSON-LD objects on a page, flattened through arrays and @graph."""
    out = []
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        page, re.S | re.I,
    ):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                out.append(item)
                for g in item.get("@graph", []) or []:
                    if isinstance(g, dict):
                        out.append(g)
    return out


def jsonld_of_type(blocks, *types):
    for b in blocks:
        t = b.get("@type", "")
        tl = t if isinstance(t, list) else [t]
        if any(x in types for x in tl):
            return b
    return None


def robots_blocked_agents(robots_txt):
    """Which AI agents have `Disallow: /` applying to them."""
    blocked = []
    groups = []  # (set_of_agents_lower, disallows)
    agents, rules, last_was_ua = set(), [], False
    for raw in robots_txt.splitlines():
        line = raw.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "user-agent":
            if not last_was_ua and agents:
                groups.append((agents, rules))
                agents, rules = set(), []
            agents.add(val.lower())
            last_was_ua = True
        elif key in ("disallow", "allow"):
            rules.append((key, val))
            last_was_ua = False
    if agents:
        groups.append((agents, rules))
    for agent, _label in AI_AGENTS:
        al = agent.lower()
        for agent_set, rules in groups:
            if al in agent_set:
                dis = [v for k, v in rules if k == "disallow"]
                alw = [v for k, v in rules if k == "allow"]
                if "/" in dis and "/" not in alw:
                    blocked.append(agent)
                break  # most specific group wins; ignore * for this audit
    return blocked


def meta_content(page, name):
    m = re.search(
        r'<meta[^>]+name=["\']' + re.escape(name) + r'["\'][^>]+content=["\'](.*?)["\']',
        page, re.I | re.S,
    ) or re.search(
        r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']' + re.escape(name) + r'["\']',
        page, re.I | re.S,
    )
    return html_mod.unescape(m.group(1)).strip() if m else ""


def title_tag(page):
    m = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
    return strip_html(m.group(1)) if m else ""


# --------------------------------------------------------------------------- #
# The audit
# --------------------------------------------------------------------------- #

class Check:
    def __init__(self, pillar, title, status, weight, detail, fix=""):
        self.pillar, self.title, self.status = pillar, title, status
        self.weight, self.detail, self.fix = weight, detail, fix

    @property
    def severity(self):
        if self.status == "pass":
            return "pass"
        if self.status == "fail":
            return "critical" if self.weight >= 3 else "high"
        return "medium"


PILLARS = ["Agent access", "Structured data", "Catalog clarity", "Trust signals"]
PILLAR_WEIGHT = {"Agent access": .25, "Structured data": .30,
                 "Catalog clarity": .25, "Trust signals": .20}


def audit(src):
    checks = []
    add = lambda *a, **k: checks.append(Check(*a, **k))

    # ---- fetch surface -----------------------------------------------------
    st_home, home = src.get("/")
    st_robots, robots = src.get("/robots.txt")
    st_llms, _llms = src.get("/llms.txt")
    st_prod_json, prod_body = src.get("/products.json?limit=250")
    st_ship, ship = src.get("/policies/shipping-policy")
    st_ref, ref = src.get("/policies/refund-policy")
    st_contact, _c = src.get("/pages/contact")

    products = []
    if st_prod_json == 200:
        try:
            products = json.loads(prod_body).get("products", [])
        except json.JSONDecodeError:
            pass

    product_page = ""
    if products:
        _, product_page = src.get("/products/" + products[0]["handle"])

    # ---- Pillar 1 · Agent access -------------------------------------------
    add("Agent access", "Machine-readable catalog feed",
        "pass" if products else "fail", 3,
        f"/products.json is open — agents can read {len(products)} products in one request."
        if products else
        "/products.json is closed or empty. Agents fall back to scraping HTML page-by-page, and most won't bother.",
        fix="Keep the public products.json endpoint enabled; it is how agents ingest your catalog.")

    blocked = robots_blocked_agents(robots) if st_robots == 200 else []
    add("Agent access", "AI crawler access in robots.txt",
        "fail" if blocked else "pass", 3,
        ("robots.txt blocks: " + ", ".join(blocked) +
         ". Those assistants cannot legally read this store — you are invisible in their shopping answers.")
        if blocked else
        "No AI shopping crawler (GPTBot, OAI-SearchBot, ClaudeBot, Google-Extended, Perplexity, Bingbot) is blocked.",
        fix="Remove the Disallow rules for AI crawler user-agents you want sales from.")

    add("Agent access", "llms.txt guidance file",
        "pass" if st_llms == 200 else "warn", 1,
        "llms.txt present — you tell agents what matters on this site."
        if st_llms == 200 else
        "No llms.txt. Optional but cheap: a plain-text map of your store for language models.",
        fix="Publish /llms.txt with your top collections, policies, and brand one-liner.")

    has_sitemap = ("sitemap" in robots.lower()) or src.get("/sitemap.xml")[0] == 200
    add("Agent access", "Sitemap discoverable",
        "pass" if has_sitemap else "fail", 2,
        "Sitemap found." if has_sitemap else "No sitemap found via robots.txt or /sitemap.xml.",
        fix="Expose /sitemap.xml and reference it from robots.txt.")

    # ---- Pillar 2 · Structured data ----------------------------------------
    pblocks = extract_jsonld(product_page)
    prod_ld = jsonld_of_type(pblocks, "Product")
    add("Structured data", "Product JSON-LD on product pages",
        "pass" if prod_ld else "fail", 3,
        "Product schema present — agents get name, price, and availability without guessing."
        if prod_ld else
        "No Product JSON-LD found on the product page. Agents must infer price and stock from raw HTML — many will skip the product.",
        fix="Emit schema.org/Product JSON-LD on every product page (most themes can; verify it survived customization).")

    offers = {}
    if prod_ld:
        o = prod_ld.get("offers", {})
        offers = o[0] if isinstance(o, list) and o else (o if isinstance(o, dict) else {})
    add("Structured data", "Offer price + currency in schema",
        "pass" if offers.get("price") and offers.get("priceCurrency") else "fail", 3,
        f"Offer: {offers.get('price')} {offers.get('priceCurrency')}."
        if offers.get("price") and offers.get("priceCurrency") else
        "Offer schema missing price or priceCurrency. An agent that can't confirm the price will not complete a purchase.",
        fix="Include offers.price and offers.priceCurrency in Product JSON-LD.")

    add("Structured data", "Availability in schema",
        "pass" if offers.get("availability") else "fail", 2,
        "Availability declared." if offers.get("availability") else
        "No availability field. Agents deprioritize products they can't confirm are in stock.",
        fix="Emit offers.availability (schema.org/InStock etc.) per variant.")

    add("Structured data", "Brand declared",
        "pass" if prod_ld and prod_ld.get("brand") else "warn", 1,
        "Brand present in schema." if prod_ld and prod_ld.get("brand") else
        "No brand in Product schema — hurts entity matching when a shopper asks for you by name.",
        fix="Add brand to Product JSON-LD.")

    has_ids = bool(prod_ld and (prod_ld.get("sku") or prod_ld.get("gtin")
                   or prod_ld.get("gtin13") or offers.get("sku") or offers.get("gtin13")))
    add("Structured data", "SKU / GTIN identifiers",
        "pass" if has_ids else "warn", 2,
        "Product identifiers present." if has_ids else
        "No SKU/GTIN in schema. Agents use identifiers to dedupe and compare across stores; without them you lose comparison placements.",
        fix="Populate sku (and gtin where products have barcodes) in Product JSON-LD.")

    add("Structured data", "Ratings exposed (aggregateRating)",
        "pass" if prod_ld and prod_ld.get("aggregateRating") else "fail", 2,
        "aggregateRating present — your reviews count in agent ranking."
        if prod_ld and prod_ld.get("aggregateRating") else
        "Reviews are not exposed as aggregateRating schema. To an agent, this store has zero social proof — even if you have hundreds of reviews.",
        fix="Have your reviews app emit aggregateRating/review JSON-LD on product pages.")

    hblocks = extract_jsonld(home)
    org = jsonld_of_type(hblocks, "Organization", "OnlineStore", "WebSite")
    add("Structured data", "Organization schema on homepage",
        "pass" if org else "warn", 1,
        "Organization/WebSite schema present." if org else
        "No Organization schema on the homepage — weakens brand entity recognition.",
        fix="Add Organization JSON-LD (name, url, logo, sameAs socials).")

    canonical = bool(re.search(r'<link[^>]+rel=["\']canonical["\']', product_page, re.I))
    add("Structured data", "Canonical URLs on product pages",
        "pass" if canonical else "warn", 1,
        "Canonical tag present." if canonical else
        "No canonical link — variant/collection URL duplicates can split your product's identity across several URLs.",
        fix="Emit rel=canonical on product pages.")

    desc = meta_content(home, "description")
    add("Structured data", "Homepage meta description",
        "pass" if 50 <= len(desc) <= 320 else ("warn" if desc else "fail"), 1,
        f"“{desc[:140]}{'…' if len(desc) > 140 else ''}”" if desc else
        "No meta description. This is often the first sentence an agent uses to describe your entire store.",
        fix="Write a 50–160 character description that says what you sell and for whom.")

    # ---- Pillar 3 · Catalog clarity ----------------------------------------
    def pct(n, d):
        return 0 if not d else round(100.0 * n / d)

    rich = sum(1 for p in products if len(strip_html(p.get("body_html", "")).split()) >= 40)
    add("Catalog clarity", "Substantive product descriptions",
        "pass" if pct(rich, len(products)) >= 80 else
        ("warn" if pct(rich, len(products)) >= 50 else "fail"), 3,
        f"{pct(rich, len(products))}% of products have ≥40 words of real description "
        f"({rich}/{len(products)}). Agents answer questions (origin, fit, materials) straight from this text — thin copy means wrong or no answers.",
        fix="Rewrite thin product descriptions; cover the questions a shopper would ask a clerk.")

    imgs = sum(1 for p in products if p.get("images"))
    add("Catalog clarity", "Every product has imagery",
        "pass" if imgs == len(products) and products else "warn", 1,
        f"{imgs}/{len(products)} products have images.",
        fix="Add images to image-less products; multimodal agents check them.")

    typed = sum(1 for p in products if (p.get("product_type") or "").strip())
    add("Catalog clarity", "Product types categorized",
        "pass" if pct(typed, len(products)) >= 80 else "warn", 2,
        f"{pct(typed, len(products))}% of products carry a product_type. Category fields feed agents' filters (“show me pour-over gear under $40”).",
        fix="Set product_type on every product; use consistent values.")

    tagged = sum(1 for p in products if p.get("tags"))
    add("Catalog clarity", "Products tagged with attributes",
        "pass" if pct(tagged, len(products)) >= 60 else "warn", 1,
        f"{pct(tagged, len(products))}% of products have tags (roast level, origin, size…). Tags become filterable attributes in agent queries.",
        fix="Tag products with the attributes shoppers filter by.")

    titles = [p.get("title", "") for p in products]
    clean_titles = sum(1 for t in titles if t and len(t) <= 75 and not re.search(r"[!]{2,}|[A-Z]{6,}", t))
    add("Catalog clarity", "Clean, unambiguous titles",
        "pass" if pct(clean_titles, len(titles)) >= 90 else "warn", 1,
        f"{pct(clean_titles, len(titles))}% of titles are ≤75 chars without shouting or keyword stuffing.",
        fix="Name products the way a human would say them aloud.")

    ambiguous = 0
    for p in products:
        for v in p.get("variants", []):
            t = (v.get("title") or "").strip()
            if t and t != "Default Title" and re.fullmatch(r"[A-Z0-9\-/ ]{1,4}", t):
                ambiguous += 1
                break
    add("Catalog clarity", "Variant options readable by agents",
        "pass" if not ambiguous else "warn", 2,
        "Variant options are self-describing." if not ambiguous else
        f"{ambiguous} product(s) use cryptic variant codes (e.g. “S / BLK”). An agent buying “size small, black” may pick the wrong variant — or refuse to buy.",
        fix="Spell out option values: “Small”, “Black”, “Whole Bean”.")

    # ---- Pillar 4 · Trust signals -------------------------------------------
    ship_text = strip_html(ship)
    ship_ok = st_ship == 200 and len(ship_text) > 80
    ship_days = bool(re.search(r"\b\d+[\-–]?\d*\s*(business\s+)?days?\b", ship_text, re.I))
    add("Trust signals", "Shipping policy with concrete timeframe",
        "pass" if ship_ok and ship_days else ("warn" if ship_ok else "fail"), 2,
        ("Shipping policy states a delivery window — agents quote it in answers."
         if ship_days else
         "Shipping policy exists but never states how many days delivery takes.") if ship_ok else
        "No shipping policy page found. Agents composing an answer will say delivery terms are “unclear” — and rank you below stores that state them.",
        fix="Publish /policies/shipping-policy with explicit delivery windows.")

    ref_text = strip_html(ref)
    ref_ok = st_ref == 200 and len(ref_text) > 80
    ref_window = bool(re.search(r"\b\d+\s*[\-–]?\s*days?\b", ref_text, re.I))
    add("Trust signals", "Return policy with explicit window",
        "pass" if ref_ok and ref_window else ("warn" if ref_ok else "fail"), 3,
        ("Return window is explicit — a strong agent trust signal for completing checkout."
         if ref_window else
         "Return policy exists but no explicit day-count window found.") if ref_ok else
        "No refund/return policy found. Checkout agents treat missing return terms as a risk flag and steer purchases elsewhere.",
        fix="Publish /policies/refund-policy with a concrete window (e.g. “30 days”).")

    add("Trust signals", "Contact page reachable",
        "pass" if st_contact == 200 else "warn", 1,
        "Contact page found." if st_contact == 200 else
        "No /pages/contact. A reachable human is part of agents' merchant-quality scoring.",
        fix="Publish a contact page with a real email or form.")

    zero_priced = sum(
        1 for p in products for v in p.get("variants", [])
        if not float(v.get("price") or 0)
    )
    add("Trust signals", "No $0 or malformed prices live",
        "pass" if not zero_priced else "fail", 2,
        "All published variant prices are non-zero." if not zero_priced else
        f"{zero_priced} published variant(s) price at $0.00 — agents read this as either a scam signal or a data error; both kill ranking.",
        fix="Unpublish or fix zero-priced variants.")

    # ---- scores --------------------------------------------------------------
    val = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
    pillar_scores = {}
    for pillar in PILLARS:
        cs = [c for c in checks if c.pillar == pillar]
        tot = sum(c.weight for c in cs)
        pillar_scores[pillar] = round(100 * sum(val[c.status] * c.weight for c in cs) / tot)
    overall = round(sum(pillar_scores[p] * PILLAR_WEIGHT[p] for p in PILLARS))

    # ---- the agent's-eye snapshot ---------------------------------------------
    cat_counts = {}
    for p in products:
        t = (p.get("product_type") or "").strip()
        if t:
            cat_counts[t] = cat_counts.get(t, 0) + 1
    top_cat = max(cat_counts, key=cat_counts.get) if cat_counts else "products"
    tops = []
    for p in products[:3]:
        v = (p.get("variants") or [{}])[0]
        price = v.get("price")
        tops.append(f"{p.get('title','?')}" + (f" (${price})" if price else ""))
    unknowns = [c.title for c in checks if c.status == "fail"][:4]
    lens = {
        "identity": title_tag(home) or src.name,
        "summary": desc or "No store description available to the agent.",
        "catalog": f"{len(products)} products readable, mostly {top_cat}." if products
                   else "Catalog is not machine-readable.",
        "tops": tops,
        "unknowns": unknowns,
    }

    return {
        "name": src.name, "url": src.url, "checks": checks,
        "pillars": pillar_scores, "overall": overall, "lens": lens,
        "grade": grade(overall),
    }


def grade(score):
    return ("A" if score >= 90 else "B" if score >= 80 else
            "C" if score >= 70 else "D" if score >= 55 else "F")


# --------------------------------------------------------------------------- #
# Report rendering
# --------------------------------------------------------------------------- #

def esc(s):
    return html_mod.escape(str(s), quote=True)


def render(results, out_path):
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "report_template.html")
    tpl = open(tpl_path, encoding="utf-8").read()

    a = results[0]
    b = results[1] if len(results) > 1 else None

    def score_card(r, role):
        tone = "good" if r["overall"] >= 80 else ("warn" if r["overall"] >= 65 else "crit")
        return (f'<div class="score-card {tone}">'
                f'<div class="role">{esc(role)}</div>'
                f'<div class="store">{esc(r["name"])}</div>'
                f'<div class="url">{esc(r["url"])}</div>'
                f'<div class="num"><span class="g">{r["grade"]}</span>{r["overall"]}'
                f'<span class="of">/100</span></div></div>')

    cards = score_card(a, "Your store") + (score_card(b, "Competitor") if b else "")

    if b:
        gap = b["overall"] - a["overall"]
        if gap > 5:
            verdict = (f'An AI shopping agent can read <b>{esc(b["name"])}</b> almost completely. '
                       f'It can only partially read <b>{esc(a["name"])}</b> — a {gap}-point gap that decides '
                       f'who gets recommended when a shopper asks an assistant to buy.')
        elif gap < -5:
            verdict = (f'<b>{esc(a["name"])}</b> is currently more agent-readable than '
                       f'{esc(b["name"])} — a lead worth protecting as assistants take over discovery.')
        else:
            verdict = 'Both stores are similarly readable to agents — the first to fix its criticals wins the channel.'
    else:
        verdict = (f'<b>{esc(a["name"])}</b> scores {a["overall"]}/100 for agent readability. '
                   'Every failed check below is a question an AI assistant cannot answer about this store.')

    def pillar_rows():
        rows = []
        for p in PILLARS:
            sa = a["pillars"][p]
            bar_b = ""
            if b:
                sb = b["pillars"][p]
                bar_b = (f'<div class="bar"><i class="them" style="width:{sb}%"></i></div>'
                         f'<span class="pv">{sb}</span>')
            rows.append(
                f'<div class="prow"><span class="pn">{esc(p)}'
                f'<em>{int(PILLAR_WEIGHT[p]*100)}% of score</em></span>'
                f'<div class="bar"><i class="us" style="width:{sa}%"></i></div>'
                f'<span class="pv">{sa}</span>{bar_b}</div>')
        return "".join(rows)

    def lens_block(r, who):
        L = r["lens"]
        tops = "".join(f"<li>{esc(t)}</li>" for t in L["tops"]) or "<li>— nothing readable —</li>"
        unknowns = "".join(f"<li>{esc(u)}</li>" for u in L["unknowns"])
        unk = (f'<div class="unk"><span>The agent cannot verify:</span><ul>{unknowns}</ul></div>'
               if unknowns else
               '<div class="unk ok"><span>No blind spots — the agent can verify everything it needs.</span></div>')
        return (f'<div class="lens"><div class="lens-h">{esc(who)} · what the agent sees</div>'
                f'<div class="lens-id">{esc(L["identity"])}</div>'
                f'<p class="lens-sum">“{esc(L["summary"])}”</p>'
                f'<p class="lens-cat">{esc(L["catalog"])}</p>'
                f'<ul class="lens-tops">{tops}</ul>{unk}</div>')

    lenses = lens_block(a, a["name"]) + (lens_block(b, b["name"]) if b else "")

    sev_rank = {"critical": 0, "high": 1, "medium": 2}
    findings = sorted((c for c in a["checks"] if c.status != "pass"),
                      key=lambda c: (sev_rank[c.severity], -c.weight))
    frows = []
    for c in findings:
        frows.append(
            f'<div class="finding {c.severity}"><div class="fh">'
            f'<span class="sev">{c.severity}</span>'
            f'<span class="ft">{esc(c.title)}</span>'
            f'<span class="fp">{esc(c.pillar)}</span></div>'
            f'<p class="fd">{esc(c.detail)}</p>'
            f'<p class="fx"><b>Fix:</b> {esc(c.fix)}</p></div>')
    if not frows:
        frows.append('<div class="finding pass"><p class="fd">No failed checks. This store is agent-ready.</p></div>')

    passed = [c for c in a["checks"] if c.status == "pass"]
    plist = "".join(f"<li>{esc(c.title)}</li>" for c in passed)

    n_crit = sum(1 for c in findings if c.severity == "critical")
    subtitle = (f'{len(a["checks"])} checks · {len(findings)} findings · '
                f'{n_crit} critical — audited {datetime.date.today().strftime("%B %d, %Y")}')

    for token, value in {
        "@@STORE@@": esc(a["name"]), "@@SUBTITLE@@": subtitle,
        "@@CARDS@@": cards, "@@VERDICT@@": verdict,
        "@@PILLARS@@": pillar_rows(), "@@LENSES@@": lenses,
        "@@FINDINGS@@": "".join(frows), "@@PASSED@@": plist,
        "@@NPASS@@": str(len(passed)),
        "@@LEGEND@@": (f'<span class="lg us">{esc(a["name"])}</span>'
                       + (f'<span class="lg them">{esc(b["name"])}</span>' if b else "")),
    }.items():
        tpl = tpl.replace(token, value)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(tpl)


# --------------------------------------------------------------------------- #

def make_source(target, fixture):
    return FixtureSource(target) if fixture else LiveSource(target)


def main():
    ap = argparse.ArgumentParser(description="Agent-readiness audit for Shopify stores")
    ap.add_argument("target", nargs="?", help="store URL (or fixture dir with --fixture)")
    ap.add_argument("--fixture", metavar="DIR", help="audit a recorded fixture directory instead of a live URL")
    ap.add_argument("--compare", metavar="URL_OR_DIR", help="second store to audit side-by-side")
    ap.add_argument("-o", "--out", default="report.html", help="output HTML report path")
    args = ap.parse_args()

    target = args.fixture or args.target
    if not target:
        ap.error("give a store URL, or --fixture DIR")

    results = [audit(make_source(target, bool(args.fixture)))]
    print(f"[agentrank] {results[0]['name']}: {results[0]['overall']}/100 ({results[0]['grade']})")
    if args.compare:
        is_fx = os.path.isdir(args.compare)
        results.append(audit(make_source(args.compare, is_fx)))
        print(f"[agentrank] {results[1]['name']}: {results[1]['overall']}/100 ({results[1]['grade']})")

    render(results, args.out)
    print(f"[agentrank] report → {args.out}")


if __name__ == "__main__":
    main()
