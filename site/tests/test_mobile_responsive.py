#!/usr/bin/env python3
"""Test mobile responsiveness of the site"""

from playwright.sync_api import sync_playwright
import time

def test_responsive_design():
    """Test site on different viewport sizes"""

    viewports = [
        {"name": "iPhone 13", "width": 390, "height": 844},
        {"name": "iPad", "width": 768, "height": 1024},
        {"name": "Desktop", "width": 1920, "height": 1080}
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False to see the browser

        print("🔍 Testing Responsive Design...")
        print("=" * 50)

        for viewport in viewports:
            print(f"\n📱 Testing on {viewport['name']} ({viewport['width']}x{viewport['height']})")

            context = browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]}
            )
            page = context.new_page()

            # Test homepage
            page.goto("http://localhost:8080/index.html")
            time.sleep(1)

            # Take screenshot
            screenshot_name = f"screenshot_{viewport['name'].replace(' ', '_')}.png"
            page.screenshot(path=f"/Users/devos/git/media/prayer_trusting_Jesus/site/tests/{screenshot_name}")
            print(f"   📸 Screenshot saved: {screenshot_name}")

            # Check for horizontal scroll (indicates responsive issues)
            has_horizontal_scroll = page.evaluate("""
                () => {
                    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
                }
            """)

            if has_horizontal_scroll:
                print(f"   ⚠️ Horizontal scroll detected on {viewport['name']}")
            else:
                print(f"   ✅ No horizontal scroll on {viewport['name']}")

            # Check if navigation menu is accessible
            try:
                # Check if cards are visible
                cards_visible = page.is_visible('.card', timeout=2000)
                if cards_visible:
                    print(f"   ✅ Quick access cards visible")
                else:
                    print(f"   ❌ Quick access cards not visible")

            except Exception as e:
                print(f"   ❌ Error checking elements: {str(e)}")

            # Test a presentation page
            page.goto("http://localhost:8080/presentations/Gospel_of_Grace_Presentation.html")
            time.sleep(1)

            # Check if slide navigation works
            try:
                # Check for navigation buttons
                nav_visible = page.is_visible('.nav-button', timeout=2000)
                if nav_visible:
                    print(f"   ✅ Presentation navigation visible")

                    # Try clicking next button if on mobile
                    if viewport["width"] < 768:
                        page.click('.nav-button:has-text("Next")')
                        print(f"   ✅ Mobile navigation works")
                else:
                    print(f"   ❌ Presentation navigation not visible")

            except Exception as e:
                print(f"   ⚠️ Navigation test: {str(e)}")

            context.close()

        browser.close()
        print("\n" + "=" * 50)
        print("✅ Responsive design testing complete!")
        print("📁 Screenshots saved in tests folder")

if __name__ == "__main__":
    test_responsive_design()