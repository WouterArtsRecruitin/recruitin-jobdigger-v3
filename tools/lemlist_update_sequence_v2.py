"""Update Lemlist sequence Touch 1 & 2 with PDF URLs."""
import time
from playwright.sync_api import sync_playwright

CAMPAIGN_ID = "cam_B3BDF7MeBCcTN3CtS"
LEMLIST_EMAIL = "wouter.arts@recruitin.nl"
LEMLIST_PASSWORD = "Recruitin2026!"

TOUCHES = {
    1: {
        "old_subject": "Vacature-analyse voor {{companyName}}",
        "new_subject": "Kandidaatprofiel voor {{jobTitle}} in {{city}}",
        "new_body": """Hi {{firstName|Beste}},

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
    2: {
        "old_subject": "Wie solliciteert op {{jobTitle}} in {{city}}?",
        "new_subject": "Wie solliciteert op {{jobTitle}} in {{city}}?",
        "new_body": """Hi {{firstName|Beste}},

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
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Login
            print("[1] Login...")
            page.goto("https://app.lemlist.com/login")
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            email_input = page.locator('input[type="email"]').first
            email_input.fill(LEMLIST_EMAIL)
            time.sleep(0.5)

            pwd_input = page.locator('input[type="password"]').first
            pwd_input.fill(LEMLIST_PASSWORD)
            pwd_input.press("Enter")
            page.wait_for_load_state("networkidle")
            time.sleep(5)
            print("  ✓ Logged in")

            # Go to campaign
            print(f"[2] Open campaign {CAMPAIGN_ID}...")
            page.goto(f"https://app.lemlist.com/campaigns/{CAMPAIGN_ID}/sequences")
            page.wait_for_load_state("networkidle")
            time.sleep(5)

            # Find and open the sequence editor
            print("[3] Opening sequence editor...")
            try:
                # Look for edit button or sequence item
                edit_btns = page.locator("button").filter(has_text="Edit").all()
                if edit_btns:
                    edit_btns[0].click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(5)
                    print("  ✓ Sequence editor opened")
            except Exception as e:
                print(f"  ⚠ Could not open editor: {e}")

            # Update each touch
            for touch_num, touch_data in TOUCHES.items():
                update_touch_in_sequence(page, touch_num, touch_data)

            print("\n✓ All updates complete!")

        finally:
            try:
                input("\nPress ENTER to close...")
            except EOFError:
                pass
            browser.close()


def update_touch_in_sequence(page, touch_num, touch_data):
    """Update a touch in the sequence editor."""
    print(f"\n[4.{touch_num}] Updating Touch {touch_num}...")

    try:
        # Find the email step with the old subject
        old_subject = touch_data["old_subject"]
        new_subject = touch_data["new_subject"]
        new_body = touch_data["new_body"]

        # Look for text containing the old subject
        subject_elements = page.locator(f"text={old_subject}").all()
        if not subject_elements:
            print(f"  ⚠ Could not find touch with subject '{old_subject}'")
            return

        # Click on it to expand/edit
        subject_elements[0].click()
        time.sleep(2)

        # Find the subject input field (usually the first input after the header)
        subject_fields = page.locator("input[type='text']").all()
        if subject_fields:
            # Find the one that matches our old subject
            for field in subject_fields:
                try:
                    val = field.get_attribute("value") or ""
                    if old_subject in val:
                        field.click()
                        time.sleep(0.3)
                        field.press("Control+A")
                        time.sleep(0.2)
                        field.type(new_subject, delay=10)
                        print(f"  ✓ Subject updated")
                        break
                except:
                    pass

        # Update body — look for contenteditable or textarea
        body_fields = page.locator('textarea, [contenteditable="true"]').all()
        if body_fields:
            # Get the last one (usually the body)
            body_field = body_fields[-1]
            body_field.click()
            time.sleep(0.5)
            body_field.press("Control+A")
            time.sleep(0.2)
            body_field.type(new_body, delay=2)
            print(f"  ✓ Body updated")

        # Save (look for Save button)
        time.sleep(1)
        save_btns = page.locator("button").filter(has_text="Save").all()
        if save_btns:
            save_btns[0].click()
            time.sleep(3)
            print(f"  ✓ Touch {touch_num} saved")
        else:
            print(f"  ⚠ Could not find Save button (may auto-save)")

    except Exception as e:
        print(f"  ✗ Error updating touch {touch_num}: {e}")


if __name__ == "__main__":
    main()
