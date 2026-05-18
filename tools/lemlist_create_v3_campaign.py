"""JobDigger V3 — Lemlist campagne aanmaken.

Lemlist API kan campagnes aanmaken maar geen email template content schrijven
(PATCH /emailTemplates → 405). Dit script:

  1. Verifieert de API key (GET /campaigns)
  2. Toont bestaande campagnes — sanity check tegen naming conflicts
  3. Maakt 'JobDigger V3 P12' aan (POST /campaigns) — DRY-RUN tenzij --apply
  4. Retourneert de campaign_id voor LEMLIST_CAMPAIGN_ID

Daarna handmatig in Lemlist UI:
  - Touch 1: koppel `templates/touch1_vacature.html` PDF (pipeline genereert per lead)
  - Touch 2: koppel `templates/touch2_doelgroep.html` PDF (idem)
  - Touch 3: copy uit `lemlist/touch3_followup.md`, delay 5d
  - Touch 4: copy uit `lemlist/touch4_insight.md`, delay 4d (=dag 9-10)
  - Touch 5: copy uit `lemlist/touch5_breakup.md`, delay 4-5d (=dag 14)
  - Schedule: 10:00 + 14:00 CET
  - Reply detection: AAN
  - Unsubscribe: AAN

Usage:
    LEMLIST_API_KEY=$(grep '^LEMLIST_API_KEY=' ~/recruitin/.env | cut -d= -f2) \
    python tools/lemlist_create_v3_campaign.py             # dry-run
    python tools/lemlist_create_v3_campaign.py --apply     # actually create
"""

from __future__ import annotations

import argparse
import os
import sys
from base64 import b64encode

import requests

API_BASE = "https://api.lemlist.com/api"
CAMPAIGN_NAME = "JobDigger V3 P12"
FROM_EMAIL = "warts@recruitin.nl"

# Existing campaigns we should NOT overwrite (from lemlist-api.md)
EXISTING_IDS = {
    "cam_8KGpG2G5ppSrwy6v4": "P12 Stage 2 (actief)",
    "cam_rkPQbJ8w7QbAkWSGJ": "P13 ICP Top",
    "cam_mB5MTdo9CWCsCrLfw": "P14 Corporate Recruiter",
}


def auth_header(api_key: str) -> dict[str, str]:
    """Lemlist gebruikt Basic auth: empty-username:api_key."""
    token = b64encode(f":{api_key}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def verify(api_key: str) -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/campaigns",
        headers=auth_header(api_key),
        params={"limit": 100},
        timeout=15,
    )
    if resp.status_code == 401:
        sys.exit("✗ Lemlist API key ongeldig (401)")
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "campaigns" in data:
        data = data["campaigns"]
    return data


def find_existing_v3(campaigns: list[dict]) -> str | None:
    for c in campaigns:
        if c.get("name") == CAMPAIGN_NAME:
            return c.get("_id") or c.get("id")
    return None


def create_campaign(api_key: str) -> str:
    resp = requests.post(
        f"{API_BASE}/campaigns",
        headers={**auth_header(api_key), "Content-Type": "application/json"},
        json={"name": CAMPAIGN_NAME},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("_id") or data.get("id") or data.get("campaign", {}).get("_id")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="Daadwerkelijk aanmaken (default: dry-run preview)"
    )
    args = parser.parse_args()

    api_key = os.environ.get("LEMLIST_API_KEY")
    if not api_key:
        sys.exit("✗ LEMLIST_API_KEY niet gezet")

    print(f"[1/3] Verifieer API key & lijst campagnes")
    campaigns = verify(api_key)
    print(f"  ✓ {len(campaigns)} campagnes gevonden")

    print(f"\n[2/3] Conflict check tegen bestaande JobDigger IDs")
    for c in campaigns:
        cid = c.get("_id") or c.get("id")
        if cid in EXISTING_IDS:
            print(f"  ✓ '{c.get('name')}' ({cid}) blijft staan — niet aanraken")

    existing_v3 = find_existing_v3(campaigns)
    if existing_v3:
        print(f"\n  ⚠ '{CAMPAIGN_NAME}' bestaat al: {existing_v3}")
        print(f"  Hergebruik deze ID — set LEMLIST_CAMPAIGN_ID={existing_v3}")
        return 0

    print(f"\n[3/3] Aanmaken '{CAMPAIGN_NAME}'")
    if not args.apply:
        print("  DRY-RUN — voeg --apply toe om daadwerkelijk aan te maken")
        print(f"  POST {API_BASE}/campaigns")
        print(f'    body: {{"name": "{CAMPAIGN_NAME}"}}')
        return 0

    campaign_id = create_campaign(api_key)
    print(f"  ✓ Aangemaakt: {campaign_id}")

    print(f"\n=== Volgende stappen (handmatig in Lemlist UI) ===")
    print(f"  Open: https://app.lemlist.com/campaigns/{campaign_id}/sequence")
    print(f"  1. Voeg 5 touches toe in deze volgorde:")
    print(f"     - Touch 1 (dag 0):  PDF Vacature-analyse — pipeline upload via API")
    print(f"     - Touch 2 (dag 2):  PDF Doelgroep-rapport — pipeline upload via API")
    print(f"     - Touch 3 (dag 5):  copy uit lemlist/touch3_followup.md")
    print(f"     - Touch 4 (dag 9):  copy uit lemlist/touch4_insight.md")
    print(f"     - Touch 5 (dag 14): copy uit lemlist/touch5_breakup.md")
    print(f"  2. Schedule: 10:00 + 14:00 CET, ma-vr")
    print(f"  3. Reply detection: ON (→ Pipedrive Stage 'Lead Warm')")
    print(f"  4. Unsubscribe: ON (AVG)")
    print(f"  5. Sender: {FROM_EMAIL}")
    print(f"\n  Dan in .env.local: LEMLIST_CAMPAIGN_ID={campaign_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
