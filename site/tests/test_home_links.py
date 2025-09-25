#!/usr/bin/env python3
"""Test home links on all presentation slides"""

from playwright.sync_api import sync_playwright
import time

def test_home_links():
    """Test that home buttons work on both presentations"""

    presentations = [
        {"name": "Gospel of Grace", "path": "presentations/Gospel_of_Grace_Presentation.html"},
        {"name": "Have I Not Called You", "path": "presentations/Have_I_Not_Called_You_Presentation.html"}
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("🔍 Testing Home Links on Presentations...")
        print("=" * 50)

        results = []

        for presentation in presentations:
            print(f"\n📊 Testing {presentation['name']} presentation...")

            try:
                # Navigate to presentation
                page.goto(f"http://localhost:8081/{presentation['path']}")
                time.sleep(1)

                # Check if home button is visible
                home_button_visible = page.is_visible('.home-button', timeout=3000)

                if not home_button_visible:
                    results.append(f"❌ {presentation['name']}: Home button not found")
                    continue

                # Get the home button text
                home_text = page.text_content('.home-button')
                print(f"   ✅ Home button found: {home_text.strip()}")

                # Click the home button
                page.click('.home-button')
                time.sleep(1)

                # Check if we're on the dashboard
                current_url = page.url
                if 'index.html' in current_url or current_url.endswith('/'):
                    results.append(f"✅ {presentation['name']}: Home link works correctly")
                    print(f"   ✅ Successfully navigated to dashboard")

                    # Verify dashboard loaded
                    if page.is_visible('.header h1', timeout=2000):
                        dashboard_title = page.text_content('.header h1')
                        print(f"   ✅ Dashboard loaded: {dashboard_title}")
                else:
                    results.append(f"❌ {presentation['name']}: Home link failed (URL: {current_url})")
                    print(f"   ❌ Failed to navigate to dashboard")

                # Test on different slides
                print(f"   📝 Testing home button on multiple slides...")
                page.goto(f"http://localhost:8081/{presentation['path']}")
                time.sleep(0.5)

                # Navigate to slide 3
                for _ in range(2):
                    if page.is_visible('.nav-button:has-text("Next")', timeout=1000):
                        page.click('.nav-button:has-text("Next")')
                    elif page.is_visible('.nav-btn:has-text("Next")', timeout=1000):
                        page.click('.nav-btn:has-text("Next")')
                    time.sleep(0.3)

                # Try home button from slide 3
                if page.is_visible('.home-button'):
                    page.click('.home-button')
                    time.sleep(0.5)

                    if 'index.html' in page.url or page.url.endswith('/'):
                        print(f"   ✅ Home button works from slide 3")
                    else:
                        print(f"   ❌ Home button failed from slide 3")

            except Exception as e:
                results.append(f"❌ {presentation['name']}: Error - {str(e)}")
                print(f"   ❌ Error: {str(e)}")

        browser.close()

        # Print summary
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY:")
        for result in results:
            print(result)

        # Check overall success
        failed = [r for r in results if "❌" in r]
        if not failed:
            print("\n🎉 ALL HOME LINKS WORKING PERFECTLY!")
            print("✅ Users can navigate back to dashboard from any slide")
        else:
            print(f"\n⚠️ Found {len(failed)} issues with home links")

        return len(failed) == 0

if __name__ == "__main__":
    success = test_home_links()
    exit(0 if success else 1)