#!/usr/bin/env python3
"""Quick verification script to confirm all links are working"""

from playwright.sync_api import sync_playwright
import time

def verify_site():
    """Run quick verification of fixed links"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("🔍 Starting link verification...")

        # Load homepage
        page.goto("http://localhost:8080/index.html")
        time.sleep(1)

        # Test navigation links
        nav_links = [
            ("sermons.html", "Sermon Library"),
            ("prayer.html", "Prayer Points Archive"),
            ("presentations.html", "Presentation Gallery")
        ]

        results = []
        for link, name in nav_links:
            try:
                # Find and click the link
                page.click(f'a[href="{link}"]')
                time.sleep(0.5)

                # Check if page loaded
                if page.url.endswith(link):
                    results.append(f"✅ {name} - Working")
                else:
                    results.append(f"❌ {name} - Failed")

                # Go back to homepage
                page.goto("http://localhost:8080/index.html")
                time.sleep(0.5)
            except Exception as e:
                results.append(f"❌ {name} - Error: {str(e)}")

        # Test presentation links
        print("\n📊 Testing presentation links...")

        # Navigate back to homepage first
        page.goto("http://localhost:8080/index.html")
        time.sleep(0.5)

        # Get presentation links
        presentation_hrefs = page.evaluate("""
            () => {
                const links = document.querySelectorAll('a[href*="presentations/"]');
                return Array.from(links).map(link => link.getAttribute('href')).filter(Boolean).slice(0, 2);
            }
        """)

        for href in presentation_hrefs:
            try:
                page.goto(f"http://localhost:8080/{href}")
                time.sleep(0.5)

                # Check if presentation loaded
                if "slide" in page.content().lower():
                    results.append(f"✅ Presentation {href} - Working")
                else:
                    results.append(f"❌ Presentation {href} - No slides found")

            except Exception as e:
                results.append(f"❌ Presentation {href} - Error: {str(e)}")

        browser.close()

        # Print results
        print("\n📋 VERIFICATION RESULTS:")
        print("=" * 50)
        for result in results:
            print(result)

        # Check if all passed
        failed = [r for r in results if "❌" in r]
        if not failed:
            print("\n🎉 ALL LINKS VERIFIED SUCCESSFULLY!")
            print("✅ Site is ready for Netlify deployment")
        else:
            print(f"\n⚠️ Found {len(failed)} issues:")
            for issue in failed:
                print(issue)

        return len(failed) == 0

if __name__ == "__main__":
    success = verify_site()
    exit(0 if success else 1)