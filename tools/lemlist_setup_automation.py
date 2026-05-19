"""Lemlist V3 campaign sequence setup via Playwright automation.

One-time script to create 5 email touches for JobDigger V3 P12 campaign.
Requires: pip install playwright; playwright install chromium

Usage:
    python tools/lemlist_setup_automation.py \
      --email wouter.arts@recruitin.nl \
      --password $LEMLIST_PASSWORD \
      --campaign-id cam_B3BDF7MeBCcTN3CtS
"""

import argparse
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect, Page

TOUCHES = [
    {
        "name": "Touch 1",
        "subject": "Vacature-analyse voor {{companyName}}",
        "body": """Hoi {{firstName|Beste}},

Bijgevoegd je analyse van de {{jobTitle}}-vacature bij {{companyName}}.

Gaat je dit rapport bekijken? (link naar PDF wordt per lead gegenereerd)

—
Recruitin""",
        "delay_days": 0,
    },
    {
        "name": "Touch 2",
        "subject": "Wie solliciteert op {{jobTitle}} in {{city}}?",
        "body": """Hoi {{firstName|Beste}},

Bijgevoegd je doelgroeprapport voor {{jobTitle}} in {{city}}.

Dit rapport toont wie de ideale kandidaat is en waar je ze vindt.

Interessant? Lees de full analysis.

—
Recruitin""",
        "delay_days": 2,
    },
    {
        "name": "Touch 3",
        "subject": "Korte vraag over je {{jobTitle}}-rapport",
        "body": """Hoi {{firstName|Beste}},

Ik heb je beide PDF's gestuurd:
- Vacature-analyse
- Doelgroeprapport

Veel zouden zeggen dat deze vacature een sterkte heeft in {{sterkste_dimensie}}. Klopt dat met je indruk?

Kort ja/nee/nog-niet?

—
Recruitin""",
        "delay_days": 5,
    },
    {
        "name": "Touch 4",
        "subject": "1 cijfer over {{city}} dat opviel",
        "body": """Hoi {{firstName|Beste}},

In {{city}} zijn momenteel {{vacancies_count}} soortgelijke {{jobTitle}}-rollen openstaand.

Slechts {{qualified_candidates}}% van de sollicitanten haalt de screening.

Dat is je kans.

Wil je meer details?

—
Recruitin""",
        "delay_days": 9,
    },
    {
        "name": "Touch 5",
        "subject": "Sluit ik het dossier {{companyName}}?",
        "body": """Hoi {{firstName|Beste}},

Als ik niets van je hoor, sluit ik het dossier {{companyName}} over 3 maanden.

Daar ben je mee eens? Of wil je dat ik het open hou?

Kort antwoord volstaat 🙂

—
Recruitin""",
        "delay_days": 14,
    },
]


def main():
    parser = argparse.ArgumentParser(description="Setup Lemlist V3 campaign sequence")
    parser.add_argument("--email", required=True, help="Lemlist login email")
    parser.add_argument("--password", required=True, help="Lemlist login password")
    parser.add_argument(
        "--campaign-id",
        default="cam_B3BDF7MeBCcTN3CtS",
        help="Campaign ID (default: JobDigger V3 P12)",
    )
    args = parser.parse_args()

    context_dir = Path("/tmp/lemlist-browser-context")
    context_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-device-orientation-sensor",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        try:
            # 1. Login
            print("[1] Logging in to Lemlist...")
            page.goto("https://app.lemlist.com/login", wait_until="domcontentloaded")
            time.sleep(3)

            # Wait for email field
            page.wait_for_selector('input[type="email"]', timeout=10000)
            time.sleep(1)

            # Fill email and password
            email_field = page.locator('input[type="email"]')
            email_field.click()
            time.sleep(0.5)
            email_field.fill(args.email)
            time.sleep(0.5)

            password_field = page.locator('input[type="password"]')
            password_field.click()
            time.sleep(0.5)
            password_field.fill(args.password)
            time.sleep(1)

            # Click submit
            submit_btn = page.locator('button[type="submit"]')
            submit_btn.click()
            time.sleep(3)

            # Wait for redirect to dashboard
            page.wait_for_url("https://app.lemlist.com/**", timeout=20000)
            time.sleep(2)
            print("✓ Logged in")

            # 2. Navigate to campaign
            print(f"[2] Opening campaign {args.campaign_id}...")
            page.goto(
                f"https://app.lemlist.com/campaigns/{args.campaign_id}/sequence",
                wait_until="domcontentloaded",
            )
            time.sleep(4)
            print("✓ Campaign loaded")

            # 3. Create 5 touches
            for i, touch in enumerate(TOUCHES, 1):
                print(f"\n[3.{i}] Adding {touch['name']} (Day {touch['delay_days']})...")

                # Wait for "Add" button and click
                page.wait_for_selector("button", timeout=10000)
                add_btn = page.locator("button").filter(has_text="Add").first
                add_btn.click()
                time.sleep(2)

                # Select Email type
                email_option = page.locator("text=Email").first
                email_option.click()
                time.sleep(2)
                print(f"  - Email type selected")

                # Fill subject
                subject_field = page.locator('input[name="subject"]')
                subject_field.wait_for(timeout=5000)
                subject_field.click()
                time.sleep(0.5)
                subject_field.fill(touch["subject"])
                print(f"  - Subject: {touch['subject'][:50]}...")
                time.sleep(0.5)

                # Fill body
                body_field = page.locator('textarea[name="body"]')
                body_field.wait_for(timeout=5000)
                body_field.click()
                time.sleep(0.5)
                body_field.fill(touch["body"])
                print(f"  - Body: {len(touch['body'])} chars")
                time.sleep(0.5)

                # Set delay (if > 0)
                if touch["delay_days"] > 0:
                    delay_field = page.locator('input[name="delay"]')
                    delay_field.wait_for(timeout=5000)
                    delay_field.click()
                    time.sleep(0.3)
                    delay_field.fill(str(touch["delay_days"]))
                    print(f"  - Delay: {touch['delay_days']} days")
                    time.sleep(0.5)

                # Save touch
                save_btn = page.locator("button").filter(has_text="Save").first
                save_btn.click()
                time.sleep(2)
                print(f"  ✓ {touch['name']} saved")

            print("\n✓ All 5 touches created successfully!")
            print("\nNext steps:")
            print("1. Verify touches in Lemlist UI: " +
                  f"https://app.lemlist.com/campaigns/{args.campaign_id}/sequence")
            print("2. Configure campaign settings (schedule, reply detection, etc.)")
            print("3. Run Fase 7 canary test with: gh workflow run daily-cron.yml -f lead_batch_size=1")

            try:
                input("\nPress ENTER to close the browser...")
            except EOFError:
                pass

        except Exception as e:
            print(f"\n✗ Error: {e}")
            print("\nDebugging info:")
            print(f"  Current URL: {page.url}")
            print(f"  Page title: {page.title()}")
            try:
                input("\nPress ENTER to close the browser and see the error state...")
            except EOFError:
                pass
            sys.exit(1)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
