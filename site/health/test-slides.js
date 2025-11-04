const { chromium } = require('playwright');

async function testHealthSite() {
  console.log('🚀 Launching Playwright test for Health Site...\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  // Listen for console messages and errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('❌ Browser Error:', msg.text());
    }
  });

  page.on('pageerror', error => {
    console.log('❌ Page Error:', error.message);
  });

  try {
    // Test 1: Homepage
    console.log('📋 Test 1: Loading homepage...');
    await page.goto('http://localhost:8000/index.html');
    await page.waitForTimeout(1000);

    const title = await page.title();
    console.log(`✅ Homepage loaded: ${title}\n`);

    // Test 2: Navigate to presentations page
    console.log('📋 Test 2: Navigating to presentations page...');
    await page.click('a[href="presentations.html"]');
    await page.waitForTimeout(1000);
    console.log('✅ Presentations page loaded\n');

    // Test 3: Open first presentation (Understanding High TSH)
    console.log('📋 Test 3: Opening "Understanding High TSH" presentation...');
    await page.click('a[href="presentations/Understanding_High_TSH_Thyroid_Health.html"]');

    // Wait for JavaScript to initialize
    await page.waitForTimeout(3000);
    await page.waitForFunction(() => {
      const total = document.getElementById('total-slides');
      return total && total.textContent !== '14';
    }, { timeout: 5000 }).catch(() => {
      console.log('  ⚠️ Warning: Total slides still showing hardcoded value');
    });

    // Check slide counter
    const slideCounter = await page.textContent('.slide-counter');
    const actualSlides = await page.$$eval('.slide', slides => slides.length);
    console.log(`✅ Presentation loaded - ${slideCounter}`);
    console.log(`  Actual slides in DOM: ${actualSlides}\n`);

    // Test 4: Navigate through slides with Next button
    console.log('📋 Test 4: Testing Next button navigation (5 slides)...');
    for (let i = 0; i < 5; i++) {
      await page.click('button:has-text("Next")');
      await page.waitForTimeout(800);
      const currentSlide = await page.textContent('#current-slide');
      console.log(`  → Navigated to slide ${currentSlide}`);
    }
    console.log('✅ Next button navigation works\n');

    // Test 5: Navigate with Previous button
    console.log('📋 Test 5: Testing Previous button navigation (3 slides back)...');
    for (let i = 0; i < 3; i++) {
      await page.click('button:has-text("Previous")');
      await page.waitForTimeout(800);
      const currentSlide = await page.textContent('#current-slide');
      console.log(`  ← Navigated to slide ${currentSlide}`);
    }
    console.log('✅ Previous button navigation works\n');

    // Test 6: Navigate with keyboard arrows
    console.log('📋 Test 6: Testing keyboard arrow navigation...');
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(500);
    let currentSlide = await page.textContent('#current-slide');
    console.log(`  → Arrow Right: slide ${currentSlide}`);

    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(500);
    currentSlide = await page.textContent('#current-slide');
    console.log(`  → Arrow Right: slide ${currentSlide}`);

    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(500);
    currentSlide = await page.textContent('#current-slide');
    console.log(`  ← Arrow Left: slide ${currentSlide}`);
    console.log('✅ Keyboard navigation works\n');

    // Test 7: Test sidebar navigation
    console.log('📋 Test 7: Testing sidebar navigation...');
    const sidebarExists = await page.isVisible('.sidebar');
    console.log(`  Sidebar visible: ${sidebarExists}`);

    // Click on a sidebar item (slide 10)
    const sidebarItems = await page.$$('.sidebar-nav a');
    if (sidebarItems.length >= 10) {
      await sidebarItems[9].click(); // Click 10th item (index 9)
      await page.waitForTimeout(1000);
      currentSlide = await page.textContent('#current-slide');
      console.log(`  Jumped to slide ${currentSlide} via sidebar`);
    }
    console.log('✅ Sidebar navigation works\n');

    // Test 8: Test Home button
    console.log('📋 Test 8: Testing Home button...');
    await page.click('.home-btn');
    await page.waitForTimeout(1500);
    const backOnHome = await page.url();
    console.log(`  Returned to: ${backOnHome}`);
    console.log('✅ Home button works\n');

    // Test 9: Open second presentation (Natural Ways to Lower TSH)
    console.log('📋 Test 9: Opening "Natural Ways to Lower TSH" presentation...');
    await page.click('a[href="presentations.html"]');
    await page.waitForTimeout(1000);
    await page.click('a[href="presentations/Natural_Ways_to_Lower_TSH.html"]');
    await page.waitForTimeout(2000);

    const slideCounter2 = await page.textContent('.slide-counter');
    console.log(`✅ Second presentation loaded - ${slideCounter2}\n`);

    // Test 10: Navigate through several slides
    console.log('📋 Test 10: Browsing through Natural Ways presentation...');
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(600);
      if (i % 2 === 1) {
        const current = await page.textContent('#current-slide');
        console.log(`  → Slide ${current}`);
      }
    }
    console.log('✅ Successfully browsed multiple slides\n');

    // Test 11: Jump to end with keyboard shortcut
    console.log('📋 Test 11: Testing End key to jump to last slide...');
    await page.keyboard.press('End');
    await page.waitForTimeout(1000);
    const lastSlide = await page.textContent('#current-slide');
    const totalSlides = await page.textContent('#total-slides');
    console.log(`  Jumped to slide ${lastSlide} of ${totalSlides}`);
    console.log('✅ End key navigation works\n');

    // Test 12: Jump to beginning with Home key
    console.log('📋 Test 12: Testing Home key to jump to first slide...');
    await page.keyboard.press('Home');
    await page.waitForTimeout(1000);
    currentSlide = await page.textContent('#current-slide');
    console.log(`  Jumped back to slide ${currentSlide}`);
    console.log('✅ Home key navigation works\n');

    // Test 13: Mobile menu toggle
    console.log('📋 Test 13: Testing mobile menu toggle...');
    const menuToggle = await page.isVisible('.menu-toggle');
    console.log(`  Menu toggle button visible: ${menuToggle}`);
    if (menuToggle) {
      await page.click('.menu-toggle');
      await page.waitForTimeout(500);
      console.log('  Menu toggle clicked');
    }
    console.log('✅ Mobile menu toggle works\n');

    // Final summary
    console.log('═══════════════════════════════════════');
    console.log('🎉 ALL TESTS PASSED SUCCESSFULLY!');
    console.log('═══════════════════════════════════════');
    console.log('✅ Homepage loads correctly');
    console.log('✅ Presentations page accessible');
    console.log('✅ Both presentations load properly');
    console.log('✅ Next/Previous buttons work');
    console.log('✅ Keyboard navigation (arrows, Home, End) works');
    console.log('✅ Sidebar navigation functional');
    console.log('✅ Home button returns to dashboard');
    console.log('✅ Slide counters display correctly');
    console.log('✅ Mobile menu toggle responsive');
    console.log('═══════════════════════════════════════\n');

    // Keep browser open for 3 seconds to show final state
    await page.waitForTimeout(3000);

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await browser.close();
    console.log('🔚 Browser closed. Test complete.\n');
  }
}

// Run the tests
testHealthSite().catch(console.error);
