# Agentrank — live agent-readiness audits, deployable on Vercel

A fully self-contained web app. Once deployed, you type **any real Shopify store URL**
into the page and a Python serverless function audits it live — open catalog feed,
robots.txt rules for seven AI crawlers, JSON-LD structured data, variant clarity,
policy pages — then renders a scored report, optionally side-by-side with a competitor.

The Pilot pitch demo is bundled at `/pilot`.

```
agentrank-web/
├── index.html          # landing page + client-side report renderer (embedded sample data)
├── pilot.html          # the Pilot "AI runs your store" pitch demo
├── vercel.json         # function timeout + /pilot rewrite
└── api/
    ├── audit.py        # GET /api/audit?store=<url>[&compare=<url>]  → Vercel Python function
    └── _audit_core.py  # the 23-check audit engine (stdlib only, no requirements.txt)
```

## Deploy (2 minutes)

**Option A — Vercel CLI:**

```bash
cd agentrank-web
npx vercel          # first run: login + link project, deploys a preview
npx vercel --prod   # production deploy
```

**Option B — Vercel dashboard:** [vercel.com/new](https://vercel.com/new) → Import your
Git repository → set **Root Directory** to `agentrank-web` → Framework Preset "Other"
→ Deploy. (This folder is fully standalone — you can also copy it into its own repo
and import that.)

No environment variables, no build step, no dependencies.

## Use it

- `https://your-deployment.vercel.app` — enter a store (e.g. a real coffee roaster on
  Shopify), optionally a competitor, hit **Run the audit**.
- `https://your-deployment.vercel.app/api/audit?store=somestore.com` — raw JSON, if you
  want to script it.
- **See a sample report** works without touching the network (two fictional stores,
  audited by the same pipeline at build time) — useful as a demo fallback on stage.
- `/pilot` — the Pilot autonomous-commerce pitch demo.

## Notes

- Some large stores front their sites with aggressive bot protection and will refuse
  the auditor (ironically, that's part of the story: they're refusing AI shopping
  agents too). The page reports this gracefully.
- The function only reads public, unauthenticated surfaces and refuses private/internal
  hosts.
- Live audits are cached at the edge for 5 minutes (`s-maxage=300`).
