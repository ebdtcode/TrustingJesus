#!/usr/bin/env node
/**
 * Converts existing HTML presentations to Reveal.js format
 * Preserves content while applying the new template structure
 */

const fs = require('fs');
const path = require('path');

// Paths
const SOURCE_DIR = path.join(__dirname, '..', 'site', 'presentations');
const TARGET_DIR = path.join(__dirname, '..', 'site', 'revealjs', 'presentations');
const MONTHLY_PRAYER_SOURCE = path.join(SOURCE_DIR, 'monthly_prayer');
const MONTHLY_PRAYER_TARGET = path.join(TARGET_DIR, 'monthly_prayer');

// Ensure target directories exist
if (!fs.existsSync(TARGET_DIR)) fs.mkdirSync(TARGET_DIR, { recursive: true });
if (!fs.existsSync(MONTHLY_PRAYER_TARGET)) fs.mkdirSync(MONTHLY_PRAYER_TARGET, { recursive: true });

// Template for reveal.js presentation
function generateRevealTemplate(title, subtitle, speaker, slides, isMonthlyPrayer = false) {
    const cssPath = isMonthlyPrayer ? '../../css/theme-prayer.css' : '../css/theme-prayer.css';
    const homePath = isMonthlyPrayer ? '../index.html' : 'index.html';

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="${title} - Prayer Presentation">
    <title>${title} - Prayer Presentation</title>

    <!-- Reveal.js Core CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">

    <!-- Custom Prayer Theme -->
    <link rel="stylesheet" href="${cssPath}">

    <!-- Preconnect for performance -->
    <link rel="preconnect" href="https://cdn.jsdelivr.net">

    <style>
        .skip-link {
            position: absolute;
            top: -40px;
            left: 0;
            background: var(--accent, #ffd166);
            color: #14213d;
            padding: 8px 16px;
            text-decoration: none;
            z-index: 9999;
            font-weight: 600;
            border-radius: 0 0 8px 0;
        }
        .skip-link:focus { top: 0; }
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to content</a>

    <a href="${homePath}" class="home-btn" aria-label="Return to presentations list">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span>Home</span>
    </a>

    <div class="reveal" id="main-content">
        <div class="slides">
${slides}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
    <script>
        Reveal.initialize({
            width: 1920,
            height: 1080,
            margin: 0.04,
            minScale: 0.2,
            maxScale: 2.0,
            hash: true,
            history: true,
            hashOneBasedIndex: true,
            respondToHashChanges: true,
            navigationMode: 'linear',
            controls: true,
            controlsTutorial: true,
            controlsLayout: 'bottom-right',
            controlsBackArrows: 'faded',
            progress: true,
            slideNumber: 'c/t',
            showSlideNumber: 'all',
            transition: 'slide',
            transitionSpeed: 'default',
            backgroundTransition: 'fade',
            autoAnimate: true,
            autoAnimateDuration: 0.8,
            autoAnimateEasing: 'ease-out',
            autoAnimateUnmatched: true,
            fragments: true,
            fragmentInURL: true,
            keyboard: true,
            touch: true,
            loop: false,
            center: true,
            embedded: false,
            help: true,
            pause: true,
            previewLinks: false,
            hideInactiveCursor: true,
            hideCursorTime: 3000,
            pdfSeparateFragments: true,
            pdfMaxPagesPerSlide: 1,
        });

        // Keyboard shortcut for home
        Reveal.addKeyBinding({ keyCode: 72, key: 'H', description: 'Go to home page' }, () => {
            window.location.href = '${homePath}';
        });

        // Overview mode from URL param
        if (new URLSearchParams(window.location.search).get('overview') === 'true') {
            Reveal.addEventListener('ready', () => Reveal.toggleOverview(true));
        }

        // Announce slide changes for screen readers
        Reveal.on('slidechanged', event => {
            const slideTitle = event.currentSlide.querySelector('h1, h2, h3');
            if (slideTitle) {
                const announcement = document.createElement('div');
                announcement.setAttribute('role', 'status');
                announcement.setAttribute('aria-live', 'polite');
                announcement.setAttribute('aria-atomic', 'true');
                announcement.className = 'sr-only';
                announcement.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
                announcement.textContent = \`Slide \${event.indexh + 1}: \${slideTitle.textContent}\`;
                document.body.appendChild(announcement);
                setTimeout(() => announcement.remove(), 1000);
            }
        });
    </script>
</body>
</html>`;
}

// Parse existing HTML to extract slide content
function parseExistingPresentation(html) {
    const result = {
        title: '',
        subtitle: '',
        speaker: '',
        slides: []
    };

    // Extract title from <title> tag
    const titleMatch = html.match(/<title>([^<]+)<\/title>/i);
    if (titleMatch) {
        result.title = titleMatch[1].replace(/ - .*$/, '').trim();
    }

    // Better slide parsing - find slide divs
    // Try with data-slide first, then without
    let slideMarker = /<div[^>]*class="slide[^"]*"[^>]*data-slide="([^"]+)"[^>]*>/gi;
    const slideStarts = [];
    let match;

    while ((match = slideMarker.exec(html)) !== null) {
        slideStarts.push({
            index: match.index,
            slideNum: match[1],
            fullMatch: match[0]
        });
    }

    // If no data-slide found, try matching slides without data-slide attribute
    if (slideStarts.length === 0) {
        // Match slides by <div class="slide..." - handles various attributes
        // Matches: <div class="slide">, <div class="slide active">, <div class="slide active" data-title="...">
        slideMarker = /<div\s+class="slide(?:\s+active)?"[^>]*>/gi;
        let slideNum = 0;
        while ((match = slideMarker.exec(html)) !== null) {
            slideNum++;
            slideStarts.push({
                index: match.index,
                slideNum: String(slideNum),
                fullMatch: match[0]
            });
        }
    }

    // Extract content between slide markers
    for (let i = 0; i < slideStarts.length; i++) {
        const start = slideStarts[i];
        const contentStart = start.index + start.fullMatch.length;

        // Find the end - either next slide or navigation/script
        let contentEnd;
        if (i < slideStarts.length - 1) {
            contentEnd = slideStarts[i + 1].index;
        } else {
            // Last slide - find navigation or script
            const navIndex = html.indexOf('<div class="navigation">', contentStart);
            const scriptIndex = html.indexOf('</div>\n\n  <script', contentStart);
            const endDivScript = html.indexOf('</div>\n  <script', contentStart);

            contentEnd = Math.min(
                navIndex > 0 ? navIndex : Infinity,
                scriptIndex > 0 ? scriptIndex : Infinity,
                endDivScript > 0 ? endDivScript : Infinity,
                html.length
            );
        }

        let content = html.substring(contentStart, contentEnd).trim();

        // Remove the closing </div> of the slide wrapper and any HTML comments
        // Find the last </div> that closes the slide and remove everything after it
        const lastClosingDiv = content.lastIndexOf('</div>');
        if (lastClosingDiv > 0) {
            // Count open divs vs closing divs to find the right balance
            const openDivs = (content.match(/<div/gi) || []).length;
            const closeDivs = (content.match(/<\/div>/gi) || []).length;

            // Remove extra closing divs
            if (closeDivs > openDivs) {
                // Remove trailing </div> tags and comments
                content = content.replace(/(\s*<\/div>\s*)+(\s*<!--[^>]*-->\s*)*$/gi, '');
            }
        }

        // Remove HTML comments that describe slide numbers
        content = content.replace(/<!--\s*\d+[a-z]?\.\s*[^>]*-->/gi, '');
        content = content.replace(/<!--\s*Slide\s*\d+[^>]*-->/gi, '');

        // Clean up the content
        content = cleanSlideContent(content);

        if (content.length > 0) {
            result.slides.push({
                number: start.slideNum,
                content: content
            });
        }
    }

    // Extract title slide info
    if (result.slides.length > 0) {
        const firstSlide = result.slides[0].content;
        const h1Match = firstSlide.match(/<h1[^>]*>([^<]+)<\/h1>/i);
        if (h1Match) result.title = h1Match[1].trim();

        const subtitleMatch = firstSlide.match(/<div class="subtitle"[^>]*>([^<]+)<\/div>/i);
        if (subtitleMatch) result.subtitle = subtitleMatch[1].trim();

        // Look for speaker/church info - check all subtitle divs
        const allSubtitles = firstSlide.match(/<div class="subtitle"[^>]*>([^<]+)<\/div>/gi) || [];
        for (const sub of allSubtitles) {
            const textMatch = sub.match(/>([^<]+)</);
            if (textMatch) {
                const text = textMatch[1].trim();
                if (text.includes('Pastor') || text.includes('Bishop') || text.includes('Rev')) {
                    result.speaker = text;
                    break;
                }
            }
        }
    }

    return result;
}

// Clean and convert slide content to reveal.js format
function cleanSlideContent(content) {
    // Remove inline styles that conflict with theme
    content = content.replace(/\s*style="[^"]*margin-top:\s*\d+[^"]*"/gi, '');

    // Convert content-list to standard ul
    content = content.replace(/<div class="content-list"><ul>/gi, '<ul>');
    content = content.replace(/<\/ul><\/div>/gi, '</ul>');

    // Add fragment classes to list items (but not all at once)
    content = content.replace(/<li>/gi, '<li class="fragment fade-up">');

    // Convert scripture blocks
    content = content.replace(/<div class="scripture">/gi, '<div class="scripture">');
    content = content.replace(/<div class="scripture-text">/gi, '<p class="scripture-text">');
    content = content.replace(/<\/div>\s*<div class="scripture-ref">/gi, '</p><p class="scripture-ref">');

    // Convert call-to-action
    content = content.replace(/<div class="call-to-action">/gi, '<div class="cta">');

    // Convert prayer-points wrapper
    content = content.replace(/<div class="prayer-points"><div class="content-list">/gi, '<div class="prayer-points">');
    content = content.replace(/<\/div><\/div>(\s*<\/div>)?/gi, '</div>');

    // Convert two-column layout
    content = content.replace(/<div class="two-column">/gi, '<div class="two-columns">');

    // Clean up quote blocks
    content = content.replace(/<div class="quote">/gi, '<div class="quote"><p>');
    content = content.replace(/<\/div>(\s*)(<div class="(?:content-list|scripture|prayer)")/gi, '</p></div>$1$2');

    return content;
}

// Convert slide content to reveal.js section
function convertToRevealSlide(slideContent, slideNum, isFirst = false) {
    let sectionAttrs = '';

    if (isFirst) {
        sectionAttrs = ' data-auto-animate data-background-gradient="radial-gradient(ellipse at center, #1b263b 0%, #0d1b2a 100%)"';
    } else if (slideContent.includes('call-to-action') || slideContent.includes('cta')) {
        sectionAttrs = ' data-auto-animate';
    }

    // Check if it's a section divider (simple h2 with maybe one other element)
    const isSimpleSlide = (slideContent.match(/<h2/gi) || []).length === 1 &&
                          !slideContent.includes('<ul') &&
                          !slideContent.includes('<div class="scripture"');

    if (isSimpleSlide && !isFirst) {
        sectionAttrs = ' data-background-color="#14213d"';
    }

    return `
            <!-- Slide ${slideNum} -->
            <section${sectionAttrs}>
                ${slideContent}
            </section>`;
}

// Convert a single presentation file
function convertPresentation(sourcePath, targetPath, isMonthlyPrayer = false) {
    try {
        const html = fs.readFileSync(sourcePath, 'utf8');
        const parsed = parseExistingPresentation(html);

        if (parsed.slides.length === 0) {
            console.log(`  Skipping ${path.basename(sourcePath)} - no slides found`);
            return null;
        }

        // Convert each slide
        const revealSlides = parsed.slides.map((slide, index) => {
            return convertToRevealSlide(slide.content, slide.number, index === 0);
        }).join('\n');

        // Generate the new file
        const newHtml = generateRevealTemplate(
            parsed.title,
            parsed.subtitle,
            parsed.speaker,
            revealSlides,
            isMonthlyPrayer
        );

        // Write to target
        fs.writeFileSync(targetPath, newHtml, 'utf8');

        return {
            title: parsed.title,
            subtitle: parsed.subtitle,
            speaker: parsed.speaker,
            slides: parsed.slides.length,
            file: path.relative(path.join(__dirname, '..', 'site', 'revealjs'), targetPath)
        };
    } catch (err) {
        console.error(`  Error converting ${path.basename(sourcePath)}:`, err.message);
        return null;
    }
}

// Get presentation category from filename
function getCategory(filename) {
    const lower = filename.toLowerCase();
    if (lower.includes('prayer') || lower.includes('fasting')) return 'prayer';
    if (lower.includes('series') || lower.includes('marriage')) return 'series';
    return 'sermon';
}

// Main conversion process
function main() {
    console.log('Converting presentations to Reveal.js format...\n');

    const presentations = [];
    let converted = 0;
    let skipped = 0;

    // Convert main presentations
    console.log('Processing sermon presentations:');
    const mainFiles = fs.readdirSync(SOURCE_DIR)
        .filter(f => f.endsWith('.html') && !f.startsWith('.'));

    for (const file of mainFiles) {
        const sourcePath = path.join(SOURCE_DIR, file);
        const targetFile = file.replace('_Presentation', '').replace(/_/g, '_');
        const targetPath = path.join(TARGET_DIR, targetFile);

        // Skip if already converted (Have_I_Not_Called_You)
        if (file.includes('Have_I_Not_Called_You') && fs.existsSync(path.join(TARGET_DIR, 'Have_I_Not_Called_You.html'))) {
            console.log(`  Skipping ${file} - already converted`);
            skipped++;
            continue;
        }

        console.log(`  Converting: ${file}`);
        const result = convertPresentation(sourcePath, targetPath);

        if (result) {
            result.id = file.replace('.html', '').toLowerCase().replace(/_/g, '-');
            result.category = getCategory(file);
            presentations.push(result);
            converted++;
        } else {
            skipped++;
        }
    }

    // Convert monthly prayer presentations
    console.log('\nProcessing monthly prayer presentations:');
    if (fs.existsSync(MONTHLY_PRAYER_SOURCE)) {
        const monthlyFiles = fs.readdirSync(MONTHLY_PRAYER_SOURCE)
            .filter(f => f.endsWith('.html') && !f.startsWith('.'));

        for (const file of monthlyFiles) {
            const sourcePath = path.join(MONTHLY_PRAYER_SOURCE, file);
            const targetPath = path.join(MONTHLY_PRAYER_TARGET, file);

            console.log(`  Converting: ${file}`);
            const result = convertPresentation(sourcePath, targetPath, true);

            if (result) {
                result.id = 'monthly-' + file.replace('.html', '').toLowerCase().replace(/_/g, '-');
                result.category = 'prayer';
                result.file = 'presentations/monthly_prayer/' + file;
                presentations.push(result);
                converted++;
            } else {
                skipped++;
            }
        }
    }

    // Generate presentations data for index.html
    console.log('\nGenerating presentations data...');
    const dataFile = path.join(__dirname, '..', 'site', 'revealjs', 'presentations-data.js');
    const dataContent = `// Auto-generated presentations data
const presentations = ${JSON.stringify(presentations, null, 2)};
`;
    fs.writeFileSync(dataFile, dataContent, 'utf8');

    console.log(`\n${'='.repeat(50)}`);
    console.log(`Conversion complete!`);
    console.log(`  Converted: ${converted}`);
    console.log(`  Skipped: ${skipped}`);
    console.log(`  Total presentations: ${presentations.length}`);
    console.log(`\nData saved to: ${dataFile}`);
}

main();
