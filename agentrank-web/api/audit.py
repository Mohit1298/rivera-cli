"""Vercel serverless function: GET /api/audit?store=<url>[&compare=<url>]

Audits one or two live Shopify stores server-side and returns JSON the
frontend renders into a report. Stdlib only — no requirements.txt needed.
"""

import concurrent.futures
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from _audit_core import audit_url


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        store = (qs.get("store") or [""])[0].strip()
        compare = (qs.get("compare") or [""])[0].strip()

        if not store:
            return self._json(400, {"error": "pass ?store=<your-store-url>"})

        targets = [store] + ([compare] if compare else [])
        results, errors = [], []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            futures = [ex.submit(audit_url, t) for t in targets]
            for t, f in zip(targets, futures):
                try:
                    results.append(f.result(timeout=50))
                except Exception as e:
                    errors.append({"target": t, "error": str(e)})

        if not results:
            return self._json(502, {"error": errors[0]["error"] if errors else "audit failed",
                                    "errors": errors})
        return self._json(200, {"results": results, "errors": errors})

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "s-maxage=300, stale-while-revalidate=600")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
