"""Agentrank audit core — shared by the Vercel serverless function.

Reads only what an AI shopping agent can read from a store's public surface
and scores agent-readiness across four pillars. Stdlib only.
"""

import concurrent.futures
import html as html_mod
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

AI_AGENTS = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot",
    "Google-Extended", "PerplexityBot", "Bingbot",
]

UA = ("Mozilla/5.0 (compatible; AgentrankAudit/0.2; "
      "+agent-readiness audit run at the store owner's request)")

PILLARS = ["Agent access", "Structured data", "Catalog clarity", "Trust signals"]
PILLAR_WEIGHT = {"Agent access": .25, "Structured data": .30,
                 "Catalog clarity": .25, "Trust signals": .20}

FETCH_PATHS = ["/", "/robots.txt", "/llms.txt", "/sitemap.xml",
               "/products.json?limit=250", "/policies/shipping-policy",
               "/policies/refund-policy", "/pages/contact"]


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #

def _assert_public_host(host):
    if host in ("localhost",) or host.endswith(".local") or host.endswith(".internal"):
        raise ValueError("refusing to audit a private host")
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ValueError(f"cannot resolve host {host!r}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("refusing to audit a private address")


class Fetcher:
    def __init__(self, base_url):
        if not base_url.startswith(("http://", "https://")):
            base_url = "https://" + base_url
        p = urllib.parse.urlparse(base_url)
        if not p.netloc:
            raise ValueError(f"not a valid store URL: {base_url!r}")
        _assert_public_host(p.hostname)
        self.base = f"https://{p.netloc}"
        self.name = p.netloc.replace("www.", "")
        self.url = p.netloc
        self._cache = {}

    def get(self, path):
        if path in self._cache:
            return self._cache[path]
        req = urllib.request.Request(self.base + path, headers={
            "User-Agent": UA, "Accept": "*/*", "Accept-Language": "en",
        })
        try:
            with urllib.request.urlopen(req, timeout=9) as r:
                out = (r.status, r.read(2_500_000).decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            out = (e.code, "")
        except Exception:
            out = (0, "")
        self._cache[path] = out
        return out

    def prefetch(self, paths):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(self.get, paths))


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #

def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html_mod.unescape(s)).strip()


def extract_jsonld(page):
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
    blocked, groups = [], []
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
    for agent in AI_AGENTS:
        al = agent.lower()
        for agent_set, rls in groups:
            if al in agent_set:
                dis = [v for k, v in rls if k == "disallow"]
                alw = [v for k, v in rls if k == "allow"]
                if "/" in dis and "/" not in alw:
                    blocked.append(agent)
                break
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


def grade(score):
    return ("A" if score >= 90 else "B" if score >= 80 else
            "C" if score >= 70 else "D" if score >= 55 else "F")


# --------------------------------------------------------------------------- #
# The audit
# --------------------------------------------------------------------------- #

def audit(src):
    checks = []

    def add(pillar, title, status, weight, detail, fix=""):
        severity = ("pass" if status == "pass" else
                    "critical" if status == "fail" and weight >= 3 else
                    "high" if status == "fail" else "medium")
        checks.append({"pillar": pillar, "title": title, "status": status,
                       "weight": weight, "detail": detail, "fix": fix,
                       "severity": severity})

    if hasattr(src, "prefetch"):
        src.prefetch(FETCH_PATHS)
    st_home, home = src.get("/")
    st_robots, robots = src.get("/robots.txt")
    st_llms, _ = src.get("/llms.txt")
    st_sitemap, _sm = src.get("/sitemap.xml")
    st_prod_json, prod_body = src.get("/products.json?limit=250")
    st_ship, ship = src.get("/policies/shipping-policy")
    st_ref, ref = src.get("/policies/refund-policy")
    st_contact, _c = src.get("/pages/contact")

    if st_home in (0, 403) and st_prod_json in (0, 403) and st_robots in (0, 403):
        raise ValueError(
            "could not reach the store (connection failed or the site blocks "
            "automated requests) — no audit possible")

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
        "Keep the public products.json endpoint enabled; it is how agents ingest your catalog.")

    blocked = robots_blocked_agents(robots) if st_robots == 200 else []
    add("Agent access", "AI crawler access in robots.txt",
        "fail" if blocked else "pass", 3,
        ("robots.txt blocks: " + ", ".join(blocked) +
         ". Those assistants cannot legally read this store — you are invisible in their shopping answers.")
        if blocked else
        "No AI shopping crawler (GPTBot, OAI-SearchBot, ClaudeBot, Google-Extended, Perplexity, Bingbot) is blocked.",
        "Remove the Disallow rules for AI crawler user-agents you want sales from.")

    add("Agent access", "llms.txt guidance file",
        "pass" if st_llms == 200 else "warn", 1,
        "llms.txt present — you tell agents what matters on this site."
        if st_llms == 200 else
        "No llms.txt. Optional but cheap: a plain-text map of your store for language models.",
        "Publish /llms.txt with your top collections, policies, and brand one-liner.")

    has_sitemap = ("sitemap" in robots.lower()) or st_sitemap == 200
    add("Agent access", "Sitemap discoverable",
        "pass" if has_sitemap else "fail", 2,
        "Sitemap found." if has_sitemap else "No sitemap found via robots.txt or /sitemap.xml.",
        "Expose /sitemap.xml and reference it from robots.txt.")

    # ---- Pillar 2 · Structured data ----------------------------------------
    pblocks = extract_jsonld(product_page)
    prod_ld = jsonld_of_type(pblocks, "Product")
    add("Structured data", "Product JSON-LD on product pages",
        "pass" if prod_ld else "fail", 3,
        "Product schema present — agents get name, price, and availability without guessing."
        if prod_ld else
        "No Product JSON-LD found on the product page. Agents must infer price and stock from raw HTML — many will skip the product.",
        "Emit schema.org/Product JSON-LD on every product page (most themes can; verify it survived customization).")

    offers = {}
    if prod_ld:
        o = prod_ld.get("offers", {})
        offers = o[0] if isinstance(o, list) and o else (o if isinstance(o, dict) else {})
    add("Structured data", "Offer price + currency in schema",
        "pass" if offers.get("price") and offers.get("priceCurrency") else "fail", 3,
        f"Offer: {offers.get('price')} {offers.get('priceCurrency')}."
        if offers.get("price") and offers.get("priceCurrency") else
        "Offer schema missing price or priceCurrency. An agent that can't confirm the price will not complete a purchase.",
        "Include offers.price and offers.priceCurrency in Product JSON-LD.")

    add("Structured data", "Availability in schema",
        "pass" if offers.get("availability") else "fail", 2,
        "Availability declared." if offers.get("availability") else
        "No availability field. Agents deprioritize products they can't confirm are in stock.",
        "Emit offers.availability (schema.org/InStock etc.) per variant.")

    add("Structured data", "Brand declared",
        "pass" if prod_ld and prod_ld.get("brand") else "warn", 1,
        "Brand present in schema." if prod_ld and prod_ld.get("brand") else
        "No brand in Product schema — hurts entity matching when a shopper asks for you by name.",
        "Add brand to Product JSON-LD.")

    has_ids = bool(prod_ld and (prod_ld.get("sku") or prod_ld.get("gtin")
                   or prod_ld.get("gtin13") or offers.get("sku") or offers.get("gtin13")))
    add("Structured data", "SKU / GTIN identifiers",
        "pass" if has_ids else "warn", 2,
        "Product identifiers present." if has_ids else
        "No SKU/GTIN in schema. Agents use identifiers to dedupe and compare across stores; without them you lose comparison placements.",
        "Populate sku (and gtin where products have barcodes) in Product JSON-LD.")

    add("Structured data", "Ratings exposed (aggregateRating)",
        "pass" if prod_ld and prod_ld.get("aggregateRating") else "fail", 2,
        "aggregateRating present — your reviews count in agent ranking."
        if prod_ld and prod_ld.get("aggregateRating") else
        "Reviews are not exposed as aggregateRating schema. To an agent, this store has zero social proof — even if you have hundreds of reviews.",
        "Have your reviews app emit aggregateRating/review JSON-LD on product pages.")

    hblocks = extract_jsonld(home)
    org = jsonld_of_type(hblocks, "Organization", "OnlineStore", "WebSite")
    add("Structured data", "Organization schema on homepage",
        "pass" if org else "warn", 1,
        "Organization/WebSite schema present." if org else
        "No Organization schema on the homepage — weakens brand entity recognition.",
        "Add Organization JSON-LD (name, url, logo, sameAs socials).")

    canonical = bool(re.search(r'<link[^>]+rel=["\']canonical["\']', product_page, re.I))
    add("Structured data", "Canonical URLs on product pages",
        "pass" if canonical else "warn", 1,
        "Canonical tag present." if canonical else
        "No canonical link — variant/collection URL duplicates can split your product's identity across several URLs.",
        "Emit rel=canonical on product pages.")

    desc = meta_content(home, "description")
    add("Structured data", "Homepage meta description",
        "pass" if 50 <= len(desc) <= 320 else ("warn" if desc else "fail"), 1,
        ("“" + desc[:140] + ("…" if len(desc) > 140 else "") + "”") if desc else
        "No meta description. This is often the first sentence an agent uses to describe your entire store.",
        "Write a 50–160 character description that says what you sell and for whom.")

    # ---- Pillar 3 · Catalog clarity ----------------------------------------
    def pct(n, d):
        return 0 if not d else round(100.0 * n / d)

    rich = sum(1 for p in products if len(strip_html(p.get("body_html", "")).split()) >= 40)
    add("Catalog clarity", "Substantive product descriptions",
        "pass" if pct(rich, len(products)) >= 80 else
        ("warn" if pct(rich, len(products)) >= 50 else "fail"), 3,
        f"{pct(rich, len(products))}% of products have ≥40 words of real description "
        f"({rich}/{len(products)}). Agents answer questions (origin, fit, materials) straight from this text — thin copy means wrong or no answers.",
        "Rewrite thin product descriptions; cover the questions a shopper would ask a clerk.")

    imgs = sum(1 for p in products if p.get("images"))
    add("Catalog clarity", "Every product has imagery",
        "pass" if imgs == len(products) and products else "warn", 1,
        f"{imgs}/{len(products)} products have images.",
        "Add images to image-less products; multimodal agents check them.")

    typed = sum(1 for p in products if (p.get("product_type") or "").strip())
    add("Catalog clarity", "Product types categorized",
        "pass" if pct(typed, len(products)) >= 80 else "warn", 2,
        f"{pct(typed, len(products))}% of products carry a product_type. Category fields feed agents' filters (“show me pour-over gear under $40”).",
        "Set product_type on every product; use consistent values.")

    tagged = sum(1 for p in products if p.get("tags"))
    add("Catalog clarity", "Products tagged with attributes",
        "pass" if pct(tagged, len(products)) >= 60 else "warn", 1,
        f"{pct(tagged, len(products))}% of products have tags (attributes shoppers filter by).",
        "Tag products with the attributes shoppers filter by.")

    titles = [p.get("title", "") for p in products]
    clean_titles = sum(1 for t in titles if t and len(t) <= 75 and not re.search(r"[!]{2,}|[A-Z]{6,}", t))
    add("Catalog clarity", "Clean, unambiguous titles",
        "pass" if pct(clean_titles, len(titles)) >= 90 else "warn", 1,
        f"{pct(clean_titles, len(titles))}% of titles are ≤75 chars without shouting or keyword stuffing.",
        "Name products the way a human would say them aloud.")

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
        "Spell out option values: “Small”, “Black”, “Whole Bean”.")

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
        "Publish /policies/shipping-policy with explicit delivery windows.")

    ref_text = strip_html(ref)
    ref_ok = st_ref == 200 and len(ref_text) > 80
    ref_window = bool(re.search(r"\b\d+\s*[\-–]?\s*days?\b", ref_text, re.I))
    add("Trust signals", "Return policy with explicit window",
        "pass" if ref_ok and ref_window else ("warn" if ref_ok else "fail"), 3,
        ("Return window is explicit — a strong agent trust signal for completing checkout."
         if ref_window else
         "Return policy exists but no explicit day-count window found.") if ref_ok else
        "No refund/return policy found. Checkout agents treat missing return terms as a risk flag and steer purchases elsewhere.",
        "Publish /policies/refund-policy with a concrete window (e.g. “30 days”).")

    add("Trust signals", "Contact page reachable",
        "pass" if st_contact == 200 else "warn", 1,
        "Contact page found." if st_contact == 200 else
        "No /pages/contact. A reachable human is part of agents' merchant-quality scoring.",
        "Publish a contact page with a real email or form.")

    zero_priced = sum(
        1 for p in products for v in p.get("variants", [])
        if not float(v.get("price") or 0)
    )
    add("Trust signals", "No $0 or malformed prices live",
        "pass" if not zero_priced else "fail", 2,
        "All published variant prices are non-zero." if not zero_priced else
        f"{zero_priced} published variant(s) price at $0.00 — agents read this as either a scam signal or a data error; both kill ranking.",
        "Unpublish or fix zero-priced variants.")

    # ---- scores ---------------------------------------------------------------
    val = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
    pillar_scores = {}
    for pillar in PILLARS:
        cs = [c for c in checks if c["pillar"] == pillar]
        tot = sum(c["weight"] for c in cs)
        pillar_scores[pillar] = round(100 * sum(val[c["status"]] * c["weight"] for c in cs) / tot)
    overall = round(sum(pillar_scores[p] * PILLAR_WEIGHT[p] for p in PILLARS))

    # ---- the agent's-eye snapshot ----------------------------------------------
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
        tops.append(p.get("title", "?") + (f" (${price})" if price else ""))
    unknowns = [c["title"] for c in checks if c["status"] == "fail"][:4]

    return {
        "name": src.name, "url": src.url,
        "checks": checks, "pillars": pillar_scores,
        "overall": overall, "grade": grade(overall),
        "lens": {
            "identity": title_tag(home) or src.name,
            "summary": desc or "No store description available to the agent.",
            "catalog": (f"{len(products)} products readable, mostly {top_cat}."
                        if products else "Catalog is not machine-readable."),
            "tops": tops,
            "unknowns": unknowns,
        },
    }


def audit_url(url):
    return audit(Fetcher(url))
