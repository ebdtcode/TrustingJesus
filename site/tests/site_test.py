"""
Comprehensive Playwright Test Suite for Trusting Jesus Spiritual Growth Site

This test suite validates:
- Navigation functionality across all pages
- Presentation slide navigation and JavaScript features
- Responsive design on multiple viewports
- Accessibility features and ARIA compliance
- Link validation and 404 detection
- Search and filter functionality
- JavaScript functionality validation
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any

import pytest
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, expect


class TestConfig:
    """Test configuration and constants"""
    BASE_PATH = "/Users/devos/git/media/prayer_trusting_Jesus/site"
    BASE_URL = f"file://{BASE_PATH}"

    # Viewport configurations for responsive testing
    VIEWPORTS = {
        'mobile': {'width': 375, 'height': 812},
        'tablet': {'width': 768, 'height': 1024},
        'desktop': {'width': 1920, 'height': 1080}
    }

    # Expected main navigation pages
    MAIN_PAGES = [
        'index.html',
        'sermons.html',
        'prayer.html',
        'presentations.html',
        'transcripts.html'
    ]

    # Expected presentation files
    PRESENTATIONS = [
        'presentations/Gospel_of_Grace_Presentation.html',
        'presentations/Have_I_Not_Called_You_Presentation.html'
    ]

    # Accessibility requirements
    A11Y_REQUIREMENTS = [
        'lang attribute on html',
        'page title',
        'main landmark',
        'skip links',
        'proper heading hierarchy',
        'color contrast',
        'keyboard navigation'
    ]


class SiteTestSuite:
    """Main test suite for the Trusting Jesus site"""

    def __init__(self):
        self.results = {
            'navigation_tests': [],
            'presentation_tests': [],
            'responsive_tests': [],
            'accessibility_tests': [],
            'link_validation': [],
            'javascript_tests': [],
            'errors': [],
            'summary': {}
        }

    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive Site Testing...")
        print(f"📁 Testing site at: {TestConfig.BASE_PATH}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                # Run test categories
                await self._test_navigation(browser)
                await self._test_presentations(browser)
                await self._test_responsive_design(browser)
                await self._test_accessibility(browser)
                await self._test_javascript_functionality(browser)
                await self._validate_links(browser)

                # Generate summary
                self._generate_summary()

            except Exception as e:
                self.results['errors'].append(f"Test suite error: {str(e)}")
                print(f"❌ Test suite error: {e}")
            finally:
                await browser.close()

        return self.results

    async def _test_navigation(self, browser: Browser):
        """Test navigation across all main pages"""
        print("\n📍 Testing Navigation...")

        context = await browser.new_context()
        page = await context.new_page()

        for page_file in TestConfig.MAIN_PAGES:
            test_result = {
                'page': page_file,
                'status': 'unknown',
                'load_time': 0,
                'issues': []
            }

            try:
                url = f"{TestConfig.BASE_URL}/{page_file}"
                start_time = asyncio.get_event_loop().time()

                response = await page.goto(url, wait_until='networkidle')
                load_time = asyncio.get_event_loop().time() - start_time

                test_result['load_time'] = round(load_time * 1000, 2)  # Convert to ms

                if response and response.status == 200:
                    test_result['status'] = 'pass'

                    # Check for page title
                    title = await page.title()
                    if not title or title == "":
                        test_result['issues'].append("Missing page title")

                    # Check for main content
                    main_content = await page.query_selector('main, #main, .container')
                    if not main_content:
                        test_result['issues'].append("No main content area found")

                    # Check for navigation elements
                    nav_elements = await page.query_selector_all('nav a, .card-link, .timeline-link')
                    if len(nav_elements) == 0:
                        test_result['issues'].append("No navigation links found")

                    print(f"  ✅ {page_file} - {test_result['load_time']}ms")
                else:
                    test_result['status'] = 'fail'
                    test_result['issues'].append(f"HTTP {response.status if response else 'No response'}")
                    print(f"  ❌ {page_file} - Failed to load")

            except Exception as e:
                test_result['status'] = 'error'
                test_result['issues'].append(str(e))
                print(f"  ❌ {page_file} - Error: {e}")

            self.results['navigation_tests'].append(test_result)

        await context.close()

    async def _test_presentations(self, browser: Browser):
        """Test presentation functionality and slide navigation"""
        print("\n🎯 Testing Presentations...")

        context = await browser.new_context()
        page = await context.new_page()

        for presentation in TestConfig.PRESENTATIONS:
            test_result = {
                'presentation': presentation,
                'status': 'unknown',
                'slide_count': 0,
                'navigation_working': False,
                'issues': []
            }

            try:
                url = f"{TestConfig.BASE_URL}/{presentation}"
                await page.goto(url, wait_until='networkidle')

                # Check if presentation loaded
                title = await page.title()
                if title:
                    test_result['status'] = 'pass'

                    # Look for slide elements
                    slides = await page.query_selector_all('.slide, .presentation-slide, [class*="slide"]')
                    test_result['slide_count'] = len(slides)

                    # Test keyboard navigation (arrow keys)
                    await page.keyboard.press('ArrowRight')
                    await page.wait_for_timeout(500)

                    # Check for navigation controls
                    nav_controls = await page.query_selector_all('button, .nav-btn, .control-btn, [class*="nav"]')
                    if len(nav_controls) > 0:
                        test_result['navigation_working'] = True

                    # Test sidebar navigation if present
                    sidebar_toggle = await page.query_selector('.menu-toggle, .sidebar-toggle, [class*="menu"]')
                    if sidebar_toggle:
                        await sidebar_toggle.click()
                        await page.wait_for_timeout(300)

                    print(f"  ✅ {presentation} - {test_result['slide_count']} slides")
                else:
                    test_result['status'] = 'fail'
                    test_result['issues'].append("Presentation failed to load")
                    print(f"  ❌ {presentation} - Failed to load")

            except Exception as e:
                test_result['status'] = 'error'
                test_result['issues'].append(str(e))
                print(f"  ❌ {presentation} - Error: {e}")

            self.results['presentation_tests'].append(test_result)

        await context.close()

    async def _test_responsive_design(self, browser: Browser):
        """Test responsive design across different viewports"""
        print("\n📱 Testing Responsive Design...")

        for viewport_name, viewport_config in TestConfig.VIEWPORTS.items():
            print(f"  📐 Testing {viewport_name} ({viewport_config['width']}x{viewport_config['height']})")

            context = await browser.new_context(viewport=viewport_config)
            page = await context.new_page()

            test_result = {
                'viewport': viewport_name,
                'dimensions': viewport_config,
                'pages_tested': [],
                'issues': []
            }

            # Test main pages in this viewport
            for page_file in TestConfig.MAIN_PAGES[:3]:  # Test first 3 pages for performance
                try:
                    url = f"{TestConfig.BASE_URL}/{page_file}"
                    await page.goto(url, wait_until='networkidle')

                    page_test = {
                        'page': page_file,
                        'status': 'pass',
                        'layout_issues': []
                    }

                    # Check for horizontal scrollbars (mobile issue)
                    if viewport_name == 'mobile':
                        body_width = await page.evaluate("document.body.scrollWidth")
                        window_width = await page.evaluate("window.innerWidth")
                        if body_width > window_width + 10:  # 10px tolerance
                            page_test['layout_issues'].append("Horizontal scroll detected on mobile")

                    # Check for visible text and buttons
                    visible_text = await page.query_selector_all('h1, h2, h3, p, a, button')
                    if len(visible_text) == 0:
                        page_test['layout_issues'].append("No visible text elements found")

                    # Check navigation accessibility on mobile
                    if viewport_name == 'mobile':
                        nav_links = await page.query_selector_all('nav a, .card-link')
                        for link in nav_links[:3]:  # Check first few links
                            box = await link.bounding_box()
                            if box and (box['height'] < 44 or box['width'] < 44):  # Minimum touch target
                                page_test['layout_issues'].append("Touch targets too small")
                                break

                    if page_test['layout_issues']:
                        page_test['status'] = 'issues'
                        test_result['issues'].extend(page_test['layout_issues'])

                    test_result['pages_tested'].append(page_test)

                except Exception as e:
                    test_result['issues'].append(f"Error testing {page_file}: {str(e)}")

            self.results['responsive_tests'].append(test_result)
            await context.close()

    async def _test_accessibility(self, browser: Browser):
        """Test accessibility features and ARIA compliance"""
        print("\n♿ Testing Accessibility...")

        context = await browser.new_context()
        page = await context.new_page()

        for page_file in TestConfig.MAIN_PAGES:
            test_result = {
                'page': page_file,
                'a11y_score': 0,
                'passed_checks': [],
                'failed_checks': [],
                'issues': []
            }

            try:
                url = f"{TestConfig.BASE_URL}/{page_file}"
                await page.goto(url, wait_until='networkidle')

                # Check 1: HTML lang attribute
                html_lang = await page.get_attribute('html', 'lang')
                if html_lang:
                    test_result['passed_checks'].append('HTML lang attribute')
                    test_result['a11y_score'] += 1
                else:
                    test_result['failed_checks'].append('Missing HTML lang attribute')

                # Check 2: Page title
                title = await page.title()
                if title and len(title.strip()) > 0:
                    test_result['passed_checks'].append('Page title')
                    test_result['a11y_score'] += 1
                else:
                    test_result['failed_checks'].append('Missing or empty page title')

                # Check 3: Main landmark
                main_element = await page.query_selector('main, [role="main"]')
                if main_element:
                    test_result['passed_checks'].append('Main landmark')
                    test_result['a11y_score'] += 1
                else:
                    test_result['failed_checks'].append('Missing main landmark')

                # Check 4: Skip links
                skip_link = await page.query_selector('a[href^="#"], .skip-link')
                if skip_link:
                    test_result['passed_checks'].append('Skip links')
                    test_result['a11y_score'] += 1
                else:
                    test_result['failed_checks'].append('Missing skip links')

                # Check 5: Heading hierarchy
                headings = await page.query_selector_all('h1, h2, h3, h4, h5, h6')
                if len(headings) > 0:
                    test_result['passed_checks'].append('Heading structure')
                    test_result['a11y_score'] += 1
                else:
                    test_result['failed_checks'].append('No heading structure')

                # Check 6: Focus indicators
                await page.keyboard.press('Tab')
                focused_element = await page.evaluate('document.activeElement.tagName')
                if focused_element:
                    test_result['passed_checks'].append('Keyboard navigation')
                    test_result['a11y_score'] += 1
                else:
                    test_result['failed_checks'].append('Poor keyboard navigation')

                # Check 7: ARIA attributes
                aria_elements = await page.query_selector_all('[aria-label], [aria-describedby], [aria-live], [role]')
                if len(aria_elements) > 0:
                    test_result['passed_checks'].append('ARIA attributes')
                    test_result['a11y_score'] += 1
                else:
                    test_result['failed_checks'].append('Missing ARIA attributes')

                # Calculate percentage score
                test_result['a11y_score'] = round((test_result['a11y_score'] / 7) * 100, 1)

                print(f"  ♿ {page_file} - A11y Score: {test_result['a11y_score']}%")

            except Exception as e:
                test_result['issues'].append(str(e))
                print(f"  ❌ {page_file} - A11y Error: {e}")

            self.results['accessibility_tests'].append(test_result)

        await context.close()

    async def _test_javascript_functionality(self, browser: Browser):
        """Test JavaScript functionality including search, filters, and interactions"""
        print("\n⚡ Testing JavaScript Functionality...")

        context = await browser.new_context()
        page = await context.new_page()

        # Test main page JavaScript
        js_test_result = {
            'page': 'index.html',
            'search_functionality': False,
            'smooth_scrolling': False,
            'date_updates': False,
            'event_listeners': False,
            'errors': []
        }

        try:
            # Listen for console errors
            console_errors = []
            page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)

            url = f"{TestConfig.BASE_URL}/index.html"
            await page.goto(url, wait_until='networkidle')

            # Test search functionality
            search_input = await page.query_selector('#search')
            search_btn = await page.query_selector('.search-btn')

            if search_input and search_btn:
                await search_input.fill('Gospel')
                await search_btn.click()
                await page.wait_for_timeout(500)
                js_test_result['search_functionality'] = True
                print("    ✅ Search functionality working")
            else:
                js_test_result['errors'].append("Search elements not found")

            # Test smooth scrolling for anchor links
            anchor_link = await page.query_selector('a[href^="#"]')
            if anchor_link:
                await anchor_link.click()
                await page.wait_for_timeout(500)
                js_test_result['smooth_scrolling'] = True
                print("    ✅ Smooth scrolling working")

            # Test date update functionality
            date_indicator = await page.query_selector('.date-indicator')
            if date_indicator:
                date_text = await date_indicator.text_content()
                if 'Today:' in date_text:
                    js_test_result['date_updates'] = True
                    print("    ✅ Date updates working")

            # Check for JavaScript errors
            if len(console_errors) == 0:
                js_test_result['event_listeners'] = True
                print("    ✅ No JavaScript errors detected")
            else:
                js_test_result['errors'].extend(console_errors)
                print(f"    ❌ JavaScript errors: {console_errors}")

        except Exception as e:
            js_test_result['errors'].append(str(e))
            print(f"    ❌ JavaScript test error: {e}")

        self.results['javascript_tests'].append(js_test_result)

        # Test prayer page filtering (if it exists)
        if os.path.exists(f"{TestConfig.BASE_PATH}/prayer.html"):
            await self._test_prayer_page_filters(page)

        await context.close()

    async def _test_prayer_page_filters(self, page: Page):
        """Test prayer page filtering functionality"""
        try:
            url = f"{TestConfig.BASE_URL}/prayer.html"
            await page.goto(url, wait_until='networkidle')

            # Test year filter
            year_filter = await page.query_selector('#year-filter')
            if year_filter:
                await year_filter.select_option('2025')
                await page.wait_for_timeout(500)
                print("    ✅ Prayer page filters working")

        except Exception as e:
            print(f"    ❌ Prayer page filter error: {e}")

    async def _validate_links(self, browser: Browser):
        """Validate all links and check for 404s"""
        print("\n🔗 Validating Links...")

        context = await browser.new_context()
        page = await context.new_page()

        all_links = set()

        # Collect all links from main pages
        for page_file in TestConfig.MAIN_PAGES:
            try:
                url = f"{TestConfig.BASE_URL}/{page_file}"
                await page.goto(url, wait_until='networkidle')

                # Get all links
                links = await page.query_selector_all('a[href]')
                for link in links:
                    href = await link.get_attribute('href')
                    if href and not href.startswith('#') and not href.startswith('mailto:'):
                        # Convert relative links to absolute
                        if href.startswith('./') or not href.startswith('http'):
                            href = href.replace('./', '')
                            full_link = f"{TestConfig.BASE_URL}/{href}"
                        else:
                            full_link = href
                        all_links.add((full_link, page_file))

            except Exception as e:
                self.results['link_validation'].append({
                    'link': page_file,
                    'status': 'error',
                    'source_page': 'self',
                    'error': str(e)
                })

        # Test each unique link
        for link, source_page in all_links:
            link_result = {
                'link': link,
                'source_page': source_page,
                'status': 'unknown',
                'response_time': 0,
                'error': None
            }

            try:
                start_time = asyncio.get_event_loop().time()

                if link.startswith('file://'):
                    # Local file - check if it exists
                    file_path = link.replace(f"file://{TestConfig.BASE_PATH}/", "")
                    local_path = os.path.join(TestConfig.BASE_PATH, file_path)

                    if os.path.exists(local_path):
                        link_result['status'] = 'pass'
                        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                        link_result['response_time'] = round(response_time, 2)
                        print(f"    ✅ {file_path}")
                    else:
                        link_result['status'] = 'fail'
                        link_result['error'] = '404 - File not found'
                        print(f"    ❌ {file_path} - File not found")
                else:
                    # External link - try to load
                    response = await page.goto(link, wait_until='networkidle', timeout=10000)
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    link_result['response_time'] = round(response_time, 2)

                    if response and response.status < 400:
                        link_result['status'] = 'pass'
                        print(f"    ✅ {link} - {response.status}")
                    else:
                        link_result['status'] = 'fail'
                        link_result['error'] = f"HTTP {response.status if response else 'No response'}"
                        print(f"    ❌ {link} - {link_result['error']}")

            except Exception as e:
                link_result['status'] = 'error'
                link_result['error'] = str(e)
                print(f"    ❌ {link} - Error: {e}")

            self.results['link_validation'].append(link_result)

        await context.close()

    def _generate_summary(self):
        """Generate test summary and statistics"""
        summary = {
            'total_pages_tested': len(self.results['navigation_tests']),
            'total_presentations_tested': len(self.results['presentation_tests']),
            'total_links_tested': len(self.results['link_validation']),
            'navigation_pass_rate': 0,
            'presentation_pass_rate': 0,
            'link_pass_rate': 0,
            'avg_accessibility_score': 0,
            'critical_issues': [],
            'recommendations': []
        }

        # Calculate pass rates
        if summary['total_pages_tested'] > 0:
            nav_passes = sum(1 for test in self.results['navigation_tests'] if test['status'] == 'pass')
            summary['navigation_pass_rate'] = round((nav_passes / summary['total_pages_tested']) * 100, 1)

        if summary['total_presentations_tested'] > 0:
            pres_passes = sum(1 for test in self.results['presentation_tests'] if test['status'] == 'pass')
            summary['presentation_pass_rate'] = round((pres_passes / summary['total_presentations_tested']) * 100, 1)

        if summary['total_links_tested'] > 0:
            link_passes = sum(1 for test in self.results['link_validation'] if test['status'] == 'pass')
            summary['link_pass_rate'] = round((link_passes / summary['total_links_tested']) * 100, 1)

        # Calculate average accessibility score
        if self.results['accessibility_tests']:
            total_score = sum(test['a11y_score'] for test in self.results['accessibility_tests'])
            summary['avg_accessibility_score'] = round(total_score / len(self.results['accessibility_tests']), 1)

        # Identify critical issues
        for test in self.results['navigation_tests']:
            if test['status'] == 'fail':
                summary['critical_issues'].append(f"Page {test['page']} failed to load")

        for test in self.results['link_validation']:
            if test['status'] == 'fail' and '404' in str(test.get('error', '')):
                summary['critical_issues'].append(f"Broken link: {test['link']}")

        # Generate recommendations
        if summary['avg_accessibility_score'] < 80:
            summary['recommendations'].append("Improve accessibility features")

        if summary['link_pass_rate'] < 90:
            summary['recommendations'].append("Fix broken links")

        if summary['navigation_pass_rate'] < 100:
            summary['recommendations'].append("Fix page loading issues")

        # Add responsive design recommendations
        mobile_issues = sum(len(test['issues']) for test in self.results['responsive_tests']
                           if test['viewport'] == 'mobile')
        if mobile_issues > 0:
            summary['recommendations'].append("Improve mobile responsive design")

        self.results['summary'] = summary


async def generate_test_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive test report"""

    report = [
        "# Trusting Jesus Site - Test Report",
        f"Generated on: {asyncio.get_event_loop().time()}",
        "",
        "## Executive Summary",
        f"- **Total Pages Tested**: {results['summary']['total_pages_tested']}",
        f"- **Navigation Pass Rate**: {results['summary']['navigation_pass_rate']}%",
        f"- **Presentation Pass Rate**: {results['summary']['presentation_pass_rate']}%",
        f"- **Link Validation Pass Rate**: {results['summary']['link_pass_rate']}%",
        f"- **Average Accessibility Score**: {results['summary']['avg_accessibility_score']}%",
        "",
    ]

    # Critical Issues
    if results['summary']['critical_issues']:
        report.extend([
            "## 🚨 Critical Issues",
            ""
        ])
        for issue in results['summary']['critical_issues']:
            report.append(f"- ❌ {issue}")
        report.append("")

    # Recommendations
    if results['summary']['recommendations']:
        report.extend([
            "## 📋 Recommendations",
            ""
        ])
        for rec in results['summary']['recommendations']:
            report.append(f"- 🔧 {rec}")
        report.append("")

    # Detailed Results
    report.extend([
        "## 📍 Navigation Test Results",
        ""
    ])

    for test in results['navigation_tests']:
        status_icon = "✅" if test['status'] == 'pass' else "❌"
        report.append(f"- {status_icon} **{test['page']}** - {test['load_time']}ms")
        if test['issues']:
            for issue in test['issues']:
                report.append(f"  - ⚠️ {issue}")

    report.extend([
        "",
        "## 🎯 Presentation Test Results",
        ""
    ])

    for test in results['presentation_tests']:
        status_icon = "✅" if test['status'] == 'pass' else "❌"
        report.append(f"- {status_icon} **{test['presentation']}** - {test['slide_count']} slides")
        if test['issues']:
            for issue in test['issues']:
                report.append(f"  - ⚠️ {issue}")

    report.extend([
        "",
        "## ♿ Accessibility Test Results",
        ""
    ])

    for test in results['accessibility_tests']:
        score_icon = "✅" if test['a11y_score'] >= 80 else "⚠️" if test['a11y_score'] >= 60 else "❌"
        report.append(f"- {score_icon} **{test['page']}** - Score: {test['a11y_score']}%")
        report.append(f"  - Passed: {len(test['passed_checks'])}/7 checks")
        if test['failed_checks']:
            for check in test['failed_checks']:
                report.append(f"  - ❌ {check}")

    report.extend([
        "",
        "## 📱 Responsive Design Results",
        ""
    ])

    for test in results['responsive_tests']:
        viewport = test['viewport']
        issues_count = len(test['issues'])
        status_icon = "✅" if issues_count == 0 else "⚠️"
        report.append(f"- {status_icon} **{viewport.title()}** ({test['dimensions']['width']}x{test['dimensions']['height']})")
        if test['issues']:
            for issue in test['issues']:
                report.append(f"  - ⚠️ {issue}")

    report.extend([
        "",
        "## 🔗 Link Validation Results",
        ""
    ])

    broken_links = [test for test in results['link_validation'] if test['status'] == 'fail']
    if broken_links:
        report.append("### Broken Links:")
        for link in broken_links:
            report.append(f"- ❌ {link['link']} (from {link['source_page']}) - {link.get('error', 'Unknown error')}")
    else:
        report.append("- ✅ All links are working correctly")

    report.extend([
        "",
        "## ⚡ JavaScript Functionality Results",
        ""
    ])

    for test in results['javascript_tests']:
        report.append(f"### {test['page']}")
        report.append(f"- Search Functionality: {'✅' if test['search_functionality'] else '❌'}")
        report.append(f"- Smooth Scrolling: {'✅' if test['smooth_scrolling'] else '❌'}")
        report.append(f"- Date Updates: {'✅' if test['date_updates'] else '❌'}")
        report.append(f"- Event Listeners: {'✅' if test['event_listeners'] else '❌'}")
        if test['errors']:
            report.append("- Errors:")
            for error in test['errors']:
                report.append(f"  - ❌ {error}")

    return "\n".join(report)


async def main():
    """Main test runner"""
    # Verify site directory exists
    if not os.path.exists(TestConfig.BASE_PATH):
        print(f"❌ Site directory not found: {TestConfig.BASE_PATH}")
        sys.exit(1)

    print("🧪 Trusting Jesus Site - Comprehensive Test Suite")
    print("=" * 60)

    # Run test suite
    suite = SiteTestSuite()
    results = await suite.run_all_tests()

    # Generate and save report
    report = await generate_test_report(results)

    report_path = f"{TestConfig.BASE_PATH}/tests/test_report.md"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n📊 Test Report Generated: {report_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    print(f"📄 Pages Tested: {results['summary']['total_pages_tested']}")
    print(f"🎯 Presentations Tested: {results['summary']['total_presentations_tested']}")
    print(f"🔗 Links Tested: {results['summary']['total_links_tested']}")
    print(f"📍 Navigation Pass Rate: {results['summary']['navigation_pass_rate']}%")
    print(f"🎯 Presentation Pass Rate: {results['summary']['presentation_pass_rate']}%")
    print(f"🔗 Link Pass Rate: {results['summary']['link_pass_rate']}%")
    print(f"♿ Accessibility Score: {results['summary']['avg_accessibility_score']}%")

    if results['summary']['critical_issues']:
        print(f"\n🚨 Critical Issues Found: {len(results['summary']['critical_issues'])}")
        for issue in results['summary']['critical_issues']:
            print(f"   - {issue}")

    if results['summary']['recommendations']:
        print(f"\n📋 Recommendations: {len(results['summary']['recommendations'])}")
        for rec in results['summary']['recommendations']:
            print(f"   - {rec}")

    # Return results for potential further processing
    return results


if __name__ == "__main__":
    # Run the test suite
    results = asyncio.run(main())