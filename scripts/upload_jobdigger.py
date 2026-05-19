"""Manual JobDigger Excel upload to Supabase Storage.

Usage:
    python3 scripts/upload_jobdigger.py /path/to/jobdigger-vandaag.xlsx
    python3 scripts/upload_jobdigger.py ~/Downloads/opleiding-wo-hbo-actualiteit-*.xlsx

Uploads the file as `daily_vacancies_latest.xlsx` to the `jobdigger-input`
bucket (overwrites existing). The next GitHub Actions cron at 07:00 UTC
will pick it up.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

BUCKET = "jobdigger-input"
TARGET_FILENAME = "daily_vacancies_latest.xlsx"
EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-jobdigger.xlsx>", file=sys.stderr)
        return 1

    file_path = Path(sys.argv[1]).expanduser()
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        return 1
    if file_path.suffix.lower() not in {".xlsx", ".xls"}:
        print(f"ERROR: Not an Excel file: {file_path}", file=sys.stderr)
        return 1

    load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not (url and key):
        print("ERROR: SUPABASE_URL/SUPABASE_KEY not set in .env.local", file=sys.stderr)
        return 1

    size_kb = file_path.stat().st_size / 1024
    print(f"Uploading {file_path.name} ({size_kb:.1f} KB) → {BUCKET}/{TARGET_FILENAME}")

    client = create_client(url, key)
    with file_path.open("rb") as f:
        client.storage.from_(BUCKET).upload(
            path=TARGET_FILENAME,
            file=f,
            file_options={"content-type": EXCEL_MIME, "upsert": "true"},
        )
    print(f"✓ Uploaded to {BUCKET}/{TARGET_FILENAME}")
    print(f"  Pipeline will process this at next cron run (07:00 UTC daily)")
    print(f"  Or trigger manually: gh workflow run daily-cron.yml --repo WouterArtsRecruitin/recruitin-jobdigger-v3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
