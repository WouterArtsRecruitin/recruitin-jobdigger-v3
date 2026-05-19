"""Debug Lemlist campaign page structure."""
import time
from playwright.sync_api import sync_playwright

CAMPAIGN_ID = "cam_B3BDF7MeBCcTN3CtS"
LEMLIST_EMAIL = "wouter.arts@recruitin.nl"
LEMLIST_PASSWORD = "Recruitin2026!"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Login
            print("[1] Logging in...")
            page.goto("https://app.lemlist.com/login")
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            email_input = page.locator('input[type="email"]').first
            email_input.fill(LEMLIST_EMAIL)
            time.sleep(1)

            pwd_input = page.locator('input[type="password"]').first
            pwd_input.fill(LEMLIST_PASSWORD)
            time.sleep(1)

            pwd_input.press("Enter")
            page.wait_for_load_state("networkidle")
            time.sleep(5)

            # Go to campaign
            print("[2] Going to campaign...")
            page.goto(f"https://app.lemlist.com/campaigns/{CAMPAIGN_ID}/sequence")
            page.wait_for_load_state("networkidle")
            time.sleep(5)

            # Get all buttons/cards on the page
            print("\n[3] Page content analysis:")
            print(f"    Title: {page.title()}")
            print(f"    URL: {page.url}")

            # Find all text elements that might indicate touches
            all_text = page.inner_text("body")
            print(f"\n[4] All text on page (first 1000 chars):\n{all_text[:1000]}")

            # Look for touch-like elements
            buttons = page.locator("button").all()
            print(f"\n[5] Found {len(buttons)} buttons:")
            for i, btn in enumerate(buttons[:10]):
                try:
                    text = btn.inner_text()
                    if text:
                        print(f"    [{i}] {text[:50]}")
                except:
                    pass

            # Look for divs/cards that might be touches
            cards = page.locator("[class*='card'], [class*='touch'], [class*='sequence']").all()
            print(f"\n[6] Found {len(cards)} potential card/touch elements:")
            for i, card in enumerate(cards[:5]):
                try:
                    text = card.inner_text()
                    if text:
                        print(f"    [{i}] {text[:100]}")
                except:
                    pass

            print("\n[7] Keep browser open for manual inspection")
            print("    Check the page and note what you see for touches/emails")

        finally:
            try:
                input("\nPress ENTER to close...")
            except EOFError:
                pass
            browser.close()


if __name__ == "__main__":
    main()
