"""Download the latest JobDigger Excel from Supabase Storage.

Zapier uploads the daily JobDigger email-attachment to the
`jobdigger-input` bucket. This script picks the most recent file
and writes it to `data/daily_vacancies.xlsx` so the main pipeline
can process it.

Run before scripts/daily_automation.py in the GitHub Actions workflow.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from supabase import create_client

BUCKET = "jobdigger-input"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "daily_vacancies.xlsx"


def main() -> int:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not (url and key):
        print("ERROR: SUPABASE_URL/SUPABASE_KEY not set", file=sys.stderr)
        return 1

    client = create_client(url, key)
    files = client.storage.from_(BUCKET).list()
    excel_files = [
        f for f in files
        if f["name"].lower().endswith((".xlsx", ".xls")) and not f["name"].startswith(".")
    ]

    if not excel_files:
        print(f"WARNING: No Excel files in bucket '{BUCKET}'. Pipeline will fall back to JSON fixture.", file=sys.stderr)
        return 0  # non-fatal — workflow continues with fallback

    excel_files.sort(key=lambda f: f.get("updated_at") or f.get("created_at") or "", reverse=True)
    latest = excel_files[0]
    print(f"Latest JobDigger input: {latest['name']} (uploaded {latest.get('updated_at', '?')})")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    blob = client.storage.from_(BUCKET).download(latest["name"])
    OUTPUT_PATH.write_bytes(blob)
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Downloaded -> {OUTPUT_PATH} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
