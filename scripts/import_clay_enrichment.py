#!/usr/bin/env python3
"""Importeer een Clay-verrijkte CSV terug in de Lemlist-campagne.

Werkt de bestaande leads bij (PATCH) met door Clay gevonden gegevens:
  - firstName + lastName  -> ALLEEN als Clay BEIDE geeft (NAAM_REGEL)
  - linkedinUrl           -> indien gevonden
Match op het ORIGINELE contact_email (waarmee de lead is geüpload).

Gebruik:
  python scripts/import_clay_enrichment.py ~/Desktop/clay_enriched_result.csv --dry-run
  python scripts/import_clay_enrichment.py ~/Desktop/clay_enriched_result.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

import requests

API = "https://api.lemlist.com/api"

# Kolom-auto-detect (Clay-exports variëren in naamgeving). Lowercase, exact-match na strip.
EMAIL_MATCH = ["contact_email", "original_email", "email_input", "email"]
FIRST_FIELDS = ["clay_first_name", "first_name", "firstname", "voornaam", "first name", "person_first_name"]
LAST_FIELDS = ["clay_last_name", "last_name", "lastname", "achternaam", "last name", "person_last_name"]
LINKEDIN_FIELDS = ["linkedin_url", "linkedinurl", "linkedin", "person_linkedin", "linkedin profile"]


def load_env() -> dict:
    env = dict(os.environ)
    f = Path(__file__).resolve().parent.parent / ".env.local"
    if f.exists():
        for k, v in re.findall(r"^([A-Z_]+)=(.*)$", f.read_text(), re.M):
            if not env.get(k):
                env[k] = v.strip()
    return env


def is_valid_email(v: str) -> bool:
    v = (v or "").strip().lower()
    return bool(v and "@" in v and v not in ("nan", "") and "****" not in v and "." in v.split("@")[-1])


def both_names(f: str, l: str) -> bool:
    f, l = (f or "").strip(), (l or "").strip()
    return bool(f and l and f.lower() != "nan" and l.lower() != "nan")


def find(row: dict, candidates: list[str]) -> str:
    low = {k.lower().strip(): (v or "").strip() for k, v in row.items()}
    for c in candidates:
        if low.get(c) and low[c].lower() != "nan":
            return low[c]
    return ""


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        sample = f.read(2048)
        f.seek(0)
        delim = ";" if sample.count(";") > sample.count(",") else ","
        return list(csv.DictReader(f, delimiter=delim))


def patch_lead(key: str, cid: str, email: str, payload: dict) -> str:
    url = f"{API}/campaigns/{cid}/leads/{email}"
    for attempt in (1, 2):
        time.sleep(3)
        r = requests.patch(url, auth=("", key), json=payload, timeout=30)
        if r.status_code == 429 and attempt == 1:
            time.sleep(int(r.headers.get("retry-after", 60)) + 5)
            continue
        if r.status_code in (200, 201):
            return "ok"
        if r.status_code == 404:
            return "not_in_campaign"
        return f"err_{r.status_code}"
    return "err_429"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="Pad naar de Clay-verrijkte CSV")
    p.add_argument("--dry-run", action="store_true", help="Toon wat zou gebeuren, geen PATCH")
    args = p.parse_args()

    path = Path(args.csv).expanduser()
    if not path.exists():
        print(f"ERROR: bestand niet gevonden: {path}", file=sys.stderr)
        return 1

    env = load_env()
    key, cid = env.get("LEMLIST_API_KEY"), env.get("LEMLIST_CAMPAIGN_ID")
    if not (key and cid):
        print("ERROR: LEMLIST_API_KEY / LEMLIST_CAMPAIGN_ID ontbreekt", file=sys.stderr)
        return 1

    rows = read_rows(path)
    print(f"{len(rows)} rijen gelezen uit {path.name}\n")
    stats = {"patched": 0, "names": 0, "linkedin_only": 0, "skip_nodata": 0,
             "skip_noemail": 0, "not_in_campaign": 0, "failed": 0}

    for row in rows:
        email = find(row, EMAIL_MATCH).lower()
        if not is_valid_email(email):
            stats["skip_noemail"] += 1
            continue
        first, last = find(row, FIRST_FIELDS), find(row, LAST_FIELDS)
        linkedin = find(row, LINKEDIN_FIELDS)

        payload = {}
        if both_names(first, last):  # NAAM_REGEL: alleen bij BEIDE
            payload["firstName"], payload["lastName"] = first, last
        if linkedin and "linkedin.com" in linkedin.lower():
            payload["linkedinUrl"] = linkedin
        if not payload:
            stats["skip_nodata"] += 1
            continue

        label = ("naam+li" if "firstName" in payload and "linkedinUrl" in payload
                 else "naam" if "firstName" in payload else "linkedin")
        if args.dry_run:
            print(f"  [DRY] {email:38s} <- {label}: {payload.get('firstName','')} {payload.get('lastName','')} {payload.get('linkedinUrl','')[:40]}")
            stats["patched"] += 1
            if "firstName" in payload: stats["names"] += 1
            else: stats["linkedin_only"] += 1
            continue

        res = patch_lead(key, cid, email, payload)
        if res == "ok":
            stats["patched"] += 1
            if "firstName" in payload: stats["names"] += 1
            else: stats["linkedin_only"] += 1
            print(f"  ✓ {email:38s} {label}")
        elif res == "not_in_campaign":
            stats["not_in_campaign"] += 1
        else:
            stats["failed"] += 1
            print(f"  ✗ {email:38s} {res}")

    print("\n" + "=" * 50)
    print(f"  Bijgewerkt: {stats['patched']}  (naam: {stats['names']} · alleen LinkedIn: {stats['linkedin_only']})")
    print(f"  Overgeslagen: {stats['skip_nodata']} geen data · {stats['skip_noemail']} geen e-mail")
    print(f"  Niet in campagne: {stats['not_in_campaign']} · Mislukt: {stats['failed']}")
    print("=" * 50)
    if args.dry_run:
        print("DRY-RUN — niets gewijzigd. Run zonder --dry-run om te patchen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
