"""Minimal Lemlist touch creator - no network waits, just basic interactions."""
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    email = "wouter.arts@recruitin.nl"
    password = "Recruitin2026!"
    campaign_id = "cam_B3BDF7MeBCcTN3CtS"

    touches = [
        ("Touch 2", "Wie solliciteert op {{jobTitle}} in {{city}}?", "Hoi {{firstName|Beste}},\n\nBijgevoegd je doelgroeprapport voor {{jobTitle}} in {{city}}.\n\nDit rapport toont wie de ideale kandidaat is en waar je ze vindt.\n\nInteressant? Lees de full analysis.\n\n—\nRecruitin", 2),
        ("Touch 3", "Korte vraag over je {{jobTitle}}-rapport", "Hoi {{firstName|Beste}},\n\nIk heb je beide PDF's gestuurd:\n- Vacature-analyse\n- Doelgroeprapport\n\nVeel zouden zeggen dat deze vacature een sterkte heeft in {{sterkste_dimensie}}. Klopt dat met je indruk?\n\nKort ja/nee/nog-niet?\n\n—\nRecruitin", 5),
        ("Touch 4", "1 cijfer over {{city}} dat opviel", "Hoi {{firstName|Beste}},\n\nIn {{city}} zijn momenteel {{vacancies_count}} soortgelijke {{jobTitle}}-rollen openstaand.\n\nSlechts {{qualified_candidates}}% van de sollicitanten haalt de screening.\n\nDat is je kans.\n\nWil je meer details?\n\n—\nRecruitin", 9),
        ("Touch 5", "Sluit ik het dossier {{companyName}}?", "Hoi {{firstName|Beste}},\n\nAls ik niets van je hoor, sluit ik het dossier {{companyName}} over 3 maanden.\n\nDaar ben je mee eens? Of wil je dat ik het open hou?\n\nKort antwoord volstaat 🙂\n\n—\nRecruitin", 14),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        page = browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")

        try:
            # Login
            print("[1] Going to Lemlist login...")
            page.goto("https://app.lemlist.com/login")
            time.sleep(5)  # Wait for page to load visually

            # Try to find and fill email
            try:
                email_input = page.locator('input[type="email"]').first
                email_input.click()
                time.sleep(0.5)
                email_input.type(email, delay=50)
                time.sleep(1)
            except Exception as e:
                print(f"⚠ Email fill failed: {e}")

            # Try to find and fill password
            try:
                pwd_input = page.locator('input[type="password"]').first
                pwd_input.click()
                time.sleep(0.5)
                pwd_input.type(password, delay=50)
                time.sleep(1)
            except Exception as e:
                print(f"⚠ Password fill failed: {e}")

            # Try to find and click submit
            try:
                submit = page.locator('button[type="submit"]').first
                submit.click()
                time.sleep(5)  # Wait for login
            except Exception as e:
                print(f"⚠ Submit click failed: {e}")

            # Go to campaign
            print(f"[2] Going to campaign {campaign_id}...")
            page.goto(f"https://app.lemlist.com/campaigns/{campaign_id}/sequence")
            time.sleep(5)

            # Create touches
            for name, subject, body, delay in touches:
                print(f"\n[3] Adding {name}...")

                # Click Add button
                try:
                    add_btn = page.locator("button").filter(has_text="Add").first
                    add_btn.click()
                    time.sleep(2)
                except Exception as e:
                    print(f"  ⚠ Add click failed: {e}")
                    continue

                # Click Email option
                try:
                    email_opt = page.locator("text=Email").first
                    email_opt.click()
                    time.sleep(1)
                except Exception as e:
                    print(f"  ⚠ Email option failed: {e}")

                # Fill subject
                try:
                    subj_field = page.locator('input[placeholder*="ubject"], input[name*="ubject"]').first
                    subj_field.click()
                    time.sleep(0.3)
                    subj_field.type(subject, delay=10)
                    print(f"  ✓ Subject filled")
                except Exception as e:
                    print(f"  ⚠ Subject failed: {e}")

                # Fill body
                try:
                    body_field = page.locator('textarea, [contenteditable="true"]').first
                    body_field.click()
                    time.sleep(0.3)
                    body_field.type(body, delay=5)
                    print(f"  ✓ Body filled")
                except Exception as e:
                    print(f"  ⚠ Body failed: {e}")

                # Set delay
                if delay > 0:
                    try:
                        delay_field = page.locator('input[type="number"], input[name*="delay"]').first
                        delay_field.click()
                        time.sleep(0.3)
                        delay_field.type(str(delay), delay=50)
                        print(f"  ✓ Delay set to {delay} days")
                    except Exception as e:
                        print(f"  ⚠ Delay failed: {e}")

                # Save
                try:
                    save_btn = page.locator("button").filter(has_text="Save").first
                    save_btn.click()
                    time.sleep(2)
                    print(f"  ✓ {name} saved")
                except Exception as e:
                    print(f"  ⚠ Save failed: {e}")

            print("\n✓ Done!")

        finally:
            try:
                input("\nPress ENTER to close...")
            except EOFError:
                pass
            browser.close()

if __name__ == "__main__":
    main()
