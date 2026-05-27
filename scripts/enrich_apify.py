#!/usr/bin/env python3
"""Verrijk de leadlijst via Apify (Apollo-alternatief lead-database) — NAAM_REGEL-conform.

Neemt de Clay-export CSV (company_domain + contact_email), zoekt per bedrijf een
beslisser (owner/founder/c_suite/director) via de Apify lead-finder, en schrijft een
enriched CSV in het formaat dat import_clay_enrichment.py terugzet naar Lemlist:
  contact_email (origineel) , clay_first_name , clay_last_name , linkedin_url

Gebruik:
  python scripts/enrich_apify.py ~/Desktop/clay_enrichment_jobdigger.csv [--limit N]
APIFY_TOKEN wordt geladen uit ~/recruitin/.env (of env).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ACTOR = "pipelinelabs~lead-scraper-apollo-zoominfo-lusha-ppe"
SENIORITY = ["owner", "c_suite", "director", "manager"]
SENIORITY_RANK = {s: i for i, s in enumerate(SENIORITY)}  # lager = senioriteit hoger
OUT = Path("/tmp/apify_enriched.csv")


def apify_token() -> str:
    tok = os.environ.get("APIFY_TOKEN")
    if not tok:
        env = Path.home() / "recruitin" / ".env"
        if env.exists():
            m = re.search(r"^APIFY_TOKEN=(.+)$", env.read_text(), re.M)
            tok = m.group(1).strip() if m else ""
    if not tok:
        sys.exit("APIFY_TOKEN niet gevonden (env of ~/recruitin/.env)")
    return tok


def read_domains(path: Path) -> dict[str, str]:
    """domain -> origineel contact_email (eerste voorkomen)."""
    mapping: dict[str, str] = {}
    with path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            dom = (r.get("company_domain") or "").strip().lower()
            email = (r.get("contact_email") or "").strip().lower()
            if dom and "." in dom and dom not in mapping:
                mapping[dom] = email
    return mapping


def run_actor(token: str, domains: list[str], cap: int) -> list[dict]:
    base = f"https://api.apify.com/v2/acts/{ACTOR}"
    payload = {
        "companyDomainIncludes": domains,
        "seniorityIncludes": SENIORITY,
        "roleMatchMode": "any",
        "hasEmail": False,           # alleen naam nodig -> meer matches
        "totalResults": cap,
    }
    r = requests.post(f"{base}/runs?token={token}", json=payload, timeout=60)
    if r.status_code >= 400:
        sys.exit(f"Apify run-start faalde ({r.status_code}): {r.text[:300]}")
    run = r.json()["data"]
    run_id, ds_id = run["id"], run["defaultDatasetId"]
    print(f"Apify-run gestart: {run_id} ({len(domains)} domeinen, cap {cap})")
    for _ in range(120):  # max ~10 min
        time.sleep(5)
        st = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={token}", timeout=30).json()["data"]["status"]
        if st in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            print(f"  status: {st}")
            break
    items, off = [], 0
    while True:
        chunk = requests.get(
            f"https://api.apify.com/v2/datasets/{ds_id}/items",
            params={"token": token, "limit": 1000, "offset": off}, timeout=60,
        ).json()
        if not chunk:
            break
        items.extend(chunk)
        off += len(chunk)
        if len(chunk) < 1000:
            break
    return items


def pick_best(per_domain: dict[str, list[dict]]) -> dict[str, dict]:
    best = {}
    for dom, people in per_domain.items():
        people.sort(key=lambda p: SENIORITY_RANK.get((p.get("seniority") or "").lower(), 99))
        best[dom] = people[0]
    return best


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="Clay-export CSV (company_domain + contact_email)")
    p.add_argument("--limit", type=int, default=0, help="Beperk tot eerste N domeinen (test)")
    args = p.parse_args()

    token = apify_token()
    mapping = read_domains(Path(args.csv).expanduser())
    domains = list(mapping.keys())
    if args.limit:
        domains = domains[: args.limit]
    print(f"{len(domains)} domeinen te verrijken")

    # Batchgewijs (8 domeinen/run, ruim budget per domein) tegen cap-skew door grote bedrijven.
    BATCH = 8
    items: list[dict] = []
    for i in range(0, len(domains), BATCH):
        batch = domains[i:i + BATCH]
        items += run_actor(token, batch, cap=len(batch) * 8)
        print(f"  batch {i//BATCH+1}: totaal {len(items)} personen")
    print(f"Apify gaf {len(items)} personen terug")

    per_domain: dict[str, list[dict]] = {}
    for it in items:
        dom = (it.get("companyDomain") or "").strip().lower()
        if dom in mapping and it.get("firstName") and it.get("lastName"):
            per_domain.setdefault(dom, []).append(it)
    best = pick_best(per_domain)

    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["contact_email", "company_domain", "clay_first_name",
                                          "clay_last_name", "title", "linkedin_url"])
        w.writeheader()
        for dom, person in best.items():
            w.writerow({
                "contact_email": mapping[dom],
                "company_domain": dom,
                "clay_first_name": person.get("firstName", ""),
                "clay_last_name": person.get("lastName", ""),
                "title": person.get("title", ""),
                "linkedin_url": person.get("linkedinUrl", ""),
            })
    print(f"\n{len(best)}/{len(domains)} domeinen verrijkt met een beslisser-naam")
    print(f"Enriched CSV -> {OUT}")
    print("Volgende: python scripts/import_clay_enrichment.py /tmp/apify_enriched.csv --dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
