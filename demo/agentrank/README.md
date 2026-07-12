# Agentrank — agent-readiness auditor for Shopify stores

**The pitch:** when a shopper asks ChatGPT, Google, or Copilot to buy something, an AI
agent reads your store and decides whether to recommend you. Agentrank is the rank
tracker + site auditor for that new channel — Yoast/Ahrefs for the agentic-commerce era.

Unlike the Pilot demo, **this is a real, working tool**, not a simulation. It audits any
live Shopify store's public surface with ~23 concrete checks and renders a scored report.

## Run it against a real store

Zero dependencies — Python 3.8+ stdlib only:

```bash
python3 agentrank.py https://yourstore.com -o report.html
python3 agentrank.py https://yourstore.com --compare https://competitor.com -o report.html
```

> Note: the sandbox this repo was built in blocks outbound traffic to store domains, so
> the committed `sample-report.html` was generated from the recorded fixtures below.
> Run the commands above on your own machine for a live audit — same pipeline, real data.

## The bundled demo

```bash
python3 agentrank.py --fixture fixtures/driftwood --compare fixtures/hearthline -o sample-report.html
```

Driftwood Coffee Co. (the store from the Pilot demo — nice narrative continuity) scores
**62/D** against competitor Hearthline's **94/A**.

## What it checks (4 pillars, 23 checks)

- **Agent access (25%)** — open `/products.json` catalog feed; robots.txt rules for
  GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Google-Extended, PerplexityBot,
  Bingbot; llms.txt; sitemap.
- **Structured data (30%)** — Product JSON-LD; offer price/currency; availability;
  brand; SKU/GTIN; aggregateRating; Organization schema; canonicals; meta description.
- **Catalog clarity (25%)** — description depth, imagery, product_type coverage, tags,
  title quality, variant-option readability ("Small / Black", not "S / BLK").
- **Trust signals (20%)** — shipping policy with a concrete window, return policy with
  an explicit day count, contact page, no $0 prices live.

## Presenting it (60 seconds)

1. Open `sample-report.html`. Point at the two score cards: *"Same city, same beans.
   When you ask ChatGPT for coffee, it recommends the 94 — because it literally cannot
   read the 62."*
2. Scroll to **Through the agent's eyes**: Driftwood's entire brand reduced to
   *"Welcome to our online store!"* — that's what the agent has to work with.
3. The critical finding: Driftwood's robots.txt **blocks GPTBot and Perplexity**.
   (Genuinely common in the wild — merchants blocked AI crawlers in 2023–24 to stop
   training scrapes, and are now invisible to AI shoppers.)
4. Close: *"Every finding has a fix. The audit is the free wedge; monitoring your rank
   across assistants every week is the subscription."*

The kill shot in a live pitch: run it against the prospect's actual store, on stage,
while you talk.
