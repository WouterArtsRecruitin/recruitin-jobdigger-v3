"""Update Lemlist Touch 1 & 2 email templates with PDF URLs."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

CAMPAIGN_ID = "cam_B3BDF7MeBCcTN3CtS"
LEMLIST_EMAIL = "wouter.arts@recruitin.nl"
LEMLIST_PASSWORD = "Recruitin2026!"

# Touch templates from lemlist/
TOUCH_TEMPLATES = {
    "touch1": {
        "number": "1",  # Touch order in UI
        "subject": "Kandidaatprofiel voor {{jobTitle}} in {{city}}",
        "body": """Hi {{firstName|Beste}},

Bijgevoegd je snelle analyse van de {{jobTitle}}-vacature bij {{companyName}}.

Het rapport toont:
- Score op 8 aantrekkingsdimensies
- Waar jullie sterk staan, waar je voet dwars kan zetten
- Eerste 5 acties voor meer aanvragen

PDF: {{vacaturePdfUrl}}

Veel sterkte met de werving — en mocht je vragen hebben, je kent me.

Groet,
Wouter Arts — Recruitin
06-14314593 | warts@recruitin.nl""",
    },
    "touch2": {
        "number": "2",
        "subject": "Wie solliciteert op {{jobTitle}} in {{city}}?",
        "body": """Hi {{firstName|Beste}},

Vorige week stuurde ik je de vacature-analyse. Nu het doelgroepenrapport — wie is de ideale kandidaat, en waar vind je ze?

Dit rapport toont:
- Profielbeschrijving (ervaring, skills, studie)
- Waar deze kandidaten zich bevinden (locaties, sectoren, bedrijven)
- 3-5 kanalen om ze te bereiken
- Salarisverwachting in de regio

PDF: {{doelgroepPdfUrl}}

Veel succes met je werving — en bel me als je wat niet snapt.

Groet,
Wouter Arts — Recruitin
06-14314593 | warts@recruitin.nl""",
    },
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        )

        try:
            # Login
            print("[1] Login to Lemlist...")
            page.goto("https://app.lemlist.com/login")
            page.wait_for_load_state("networkidle")
            time.sleep(3)

            try:
                # Fill email
                email_input = page.locator('input[type="email"]').first
                email_input.fill(LEMLIST_EMAIL)
                time.sleep(1)

                # Fill password
                pwd_input = page.locator('input[type="password"]').first
                pwd_input.fill(LEMLIST_PASSWORD)
                time.sleep(1)

                # Press Enter to submit
                pwd_input.press("Enter")
                page.wait_for_load_state("networkidle")
                time.sleep(5)
                print("  ✓ Login complete")
            except Exception as e:
                print(f"  ✗ Login failed: {e}")
                print("  → Check browser window — may need manual action")
                time.sleep(30)  # Give user time to manually complete login
                return

            # Navigate to campaign
            print(f"[2] Go to campaign {CAMPAIGN_ID}...")
            page.goto(f"https://app.lemlist.com/campaigns/{CAMPAIGN_ID}/sequence")
            page.wait_for_load_state("networkidle")
            time.sleep(5)

            # Update Touch 1 & 2
            for touch_key, touch_data in TOUCH_TEMPLATES.items():
                update_touch(page, touch_data, touch_key)

            print("\n✓ All touches updated!")

        finally:
            try:
                input("\nPress ENTER to close...")
            except EOFError:
                pass
            browser.close()


def update_touch(page, touch_data, touch_key):
    """Update a single touch template."""
    touch_num = touch_data["number"]
    subject = touch_data["subject"]
    body = touch_data["body"]

    print(f"\n[3.{touch_num}] Updating Touch {touch_num}...")

    # Find and click the touch card (look for subject text or touch number)
    try:
        # Try to find the touch by its subject line
        touch_card = page.locator(f"text={touch_data['subject'][:20]}").first
        touch_card.click()
        time.sleep(2)
        print(f"  ✓ Found Touch {touch_num} by subject")
    except:
        print(f"  ⚠ Could not find Touch {touch_num} by subject, trying by position...")
        # Fallback: find all touch cards and click the nth one
        try:
            touches = page.locator('[data-testid*="touch"], [class*="touch"]')
            if touches.count() >= int(touch_num):
                touches.nth(int(touch_num) - 1).click()
                time.sleep(2)
                print(f"  ✓ Found Touch {touch_num} by position")
            else:
                print(f"  ✗ Could not find Touch {touch_num}")
                return
        except Exception as e:
            print(f"  ✗ Error finding touch: {e}")
            return

    # Click edit button
    try:
        edit_btn = page.locator("button").filter(has_text="Edit").first
        edit_btn.click()
        time.sleep(2)
        print(f"  ✓ Opened editor for Touch {touch_num}")
    except Exception as e:
        print(f"  ⚠ Could not find Edit button: {e}")
        return

    # Update subject
    try:
        subj_field = page.locator('input[placeholder*="ubject"], input[name*="ubject"]').first
        subj_field.triple_click()
        time.sleep(0.3)
        subj_field.type(subject, delay=10)
        print(f"  ✓ Subject updated")
    except Exception as e:
        print(f"  ⚠ Subject update failed: {e}")

    # Update body
    try:
        body_field = page.locator('textarea, [contenteditable="true"]').first
        body_field.triple_click()
        time.sleep(0.3)
        body_field.type(body, delay=5)
        print(f"  ✓ Body updated")
    except Exception as e:
        print(f"  ⚠ Body update failed: {e}")

    # Save
    try:
        save_btn = page.locator("button").filter(has_text="Save").first
        save_btn.click()
        time.sleep(2)
        print(f"  ✓ Touch {touch_num} saved")
    except Exception as e:
        print(f"  ⚠ Save failed: {e}")


if __name__ == "__main__":
    main()
