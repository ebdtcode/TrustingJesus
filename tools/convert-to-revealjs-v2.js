#!/usr/bin/env node
/**
 * Converts existing HTML presentations to Reveal.js format - Version 2
 * Uses a simpler transformation approach
 */

const fs = require('fs');
const path = require('path');

// Paths
const SOURCE_DIR = path.join(__dirname, '..', 'site', 'presentations');
const TARGET_DIR = path.join(__dirname, '..', 'site', 'modern', 'presentations');
const MONTHLY_PRAYER_SOURCE = path.join(SOURCE_DIR, 'monthly_prayer');
const MONTHLY_PRAYER_TARGET = path.join(TARGET_DIR, 'monthly_prayer');

// Generate search tags from title
function generateTags(title, category, isMonthlyPrayer) {
    const tags = [];
    const lowerTitle = title.toLowerCase();

    // Add category tags
    if (isMonthlyPrayer || category === 'prayer') {
        tags.push('prayer', 'prayer points');
    }
    if (category === 'sermon') {
        tags.push('sermon', 'message', 'teaching');
    }

    // Extract keywords from title
    const keywords = ['gospel', 'grace', 'faith', 'love', 'hope', 'prayer', 'worship',
                      'god', 'jesus', 'christ', 'holy spirit', 'bible', 'scripture',
                      'marriage', 'family', 'leadership', 'meditation', 'fasting',
                      'thanksgiving', 'angels', 'victory', 'sin', 'justification',
                      'salvation', 'names', 'born again', 'vision'];

    keywords.forEach(kw => {
        if (lowerTitle.includes(kw)) tags.push(kw);
    });

    // Month-specific tags for prayer
    const months = ['january', 'february', 'march', 'april', 'may', 'june',
                   'july', 'august', 'september', 'october', 'november', 'december'];
    months.forEach(month => {
        if (lowerTitle.includes(month)) tags.push(month, '2025', '2026');
    });

    return [...new Set(tags)]; // Remove duplicates
}

// Ensure target directories exist
if (!fs.existsSync(TARGET_DIR)) fs.mkdirSync(TARGET_DIR, { recursive: true });
if (!fs.existsSync(MONTHLY_PRAYER_TARGET)) fs.mkdirSync(MONTHLY_PRAYER_TARGET, { recursive: true });

// Extract metadata from HTML
function extractMetadata(html) {
    const titleMatch = html.match(/<title>([^<]+)<\/title>/i);
    const title = titleMatch ? titleMatch[1].replace(/ - .*$/, '').trim() : 'Presentation';

    // Try to find speaker from subtitle divs
    let speaker = '';
    const subtitleMatches = html.match(/<div class="subtitle"[^>]*>([^<]+)<\/div>/gi) || [];
    for (const sub of subtitleMatches) {
        const text = sub.match(/>([^<]+)</);
        if (text && (text[1].includes('Pastor') || text[1].includes('Bishop') || text[1].includes('Rev'))) {
            speaker = text[1].trim();
            break;
        }
    }

    return { title, speaker };
}

// Parse slides using a balanced tag approach
function parseSlides(html) {
    const slides = [];

    // Find all slide opening tags (both div and section)
    const slideOpenRegex = /<(div|section)\s+class="slide(?:\s+[^"]*)?"\s*(?:data-[^>]*)?\s*>/gi;
    let matches = [...html.matchAll(slideOpenRegex)];

    // If no matches, try with data-slide attribute (Marriage Series format)
    if (matches.length === 0) {
        const altRegex = /<(div|section)\s+[^>]*class="slide"[^>]*>/gi;
        matches = [...html.matchAll(altRegex)];
    }

    for (let i = 0; i < matches.length; i++) {
        const tagType = matches[i][1] || 'div'; // Capture group for div or section
        const startIndex = matches[i].index + matches[i][0].length;
        let endIndex;

        if (i < matches.length - 1) {
            endIndex = matches[i + 1].index;
        } else {
            // Find navigation or end of presentation
            const navMatch = html.indexOf('<div class="navigation">', startIndex);
            const scriptMatch = html.indexOf('<script>', startIndex);
            const mainClose = html.indexOf('</main>', startIndex);
            endIndex = Math.min(
                navMatch > 0 ? navMatch : html.length,
                scriptMatch > 0 ? scriptMatch : html.length,
                mainClose > 0 ? mainClose : html.length
            );
        }

        let content = html.substring(startIndex, endIndex);

        // Balance the tags - handle both div and section, remove excess closing tags
        let divDepth = 0;
        let sectionDepth = 0;
        let balancedContent = '';
        let pos = 0;

        while (pos < content.length) {
            const openDiv = content.indexOf('<div', pos);
            const closeDiv = content.indexOf('</div>', pos);
            const openSection = content.indexOf('<section', pos);
            const closeSection = content.indexOf('</section>', pos);

            // Find the nearest tag
            const positions = [
                { type: 'openDiv', pos: openDiv },
                { type: 'closeDiv', pos: closeDiv },
                { type: 'openSection', pos: openSection },
                { type: 'closeSection', pos: closeSection }
            ].filter(p => p.pos !== -1).sort((a, b) => a.pos - b.pos);

            if (positions.length === 0) {
                balancedContent += content.substring(pos);
                break;
            }

            const next = positions[0];

            if (next.type === 'openDiv') {
                const tagEnd = content.indexOf('>', next.pos);
                balancedContent += content.substring(pos, tagEnd + 1);
                divDepth++;
                pos = tagEnd + 1;
            } else if (next.type === 'closeDiv') {
                if (divDepth > 0) {
                    balancedContent += content.substring(pos, next.pos + 6);
                    divDepth--;
                } else {
                    balancedContent += content.substring(pos, next.pos);
                }
                pos = next.pos + 6;
            } else if (next.type === 'openSection') {
                const tagEnd = content.indexOf('>', next.pos);
                balancedContent += content.substring(pos, tagEnd + 1);
                sectionDepth++;
                pos = tagEnd + 1;
            } else if (next.type === 'closeSection') {
                if (sectionDepth > 0) {
                    balancedContent += content.substring(pos, next.pos + 10);
                    sectionDepth--;
                } else {
                    balancedContent += content.substring(pos, next.pos);
                }
                pos = next.pos + 10;
            }
        }

        // Close any remaining open tags
        while (divDepth > 0) {
            balancedContent += '</div>';
            divDepth--;
        }
        while (sectionDepth > 0) {
            balancedContent += '</section>';
            sectionDepth--;
        }

        // Clean up the content
        balancedContent = balancedContent
            .replace(/<!--\s*\d+[a-z]?\.\s*[^>]*-->/gi, '')  // Remove slide number comments
            .replace(/<!--\s*Slide\s*\d+[^>]*-->/gi, '')
            .replace(/^\s+|\s+$/g, '');  // Trim

        if (balancedContent.length > 0) {
            slides.push({
                number: i + 1,
                content: balancedContent
            });
        }
    }

    return slides;
}

// Clean slide content for reveal.js
function cleanContent(content) {
    // First, fix scripture divs with proper tag replacement
    // Match <div class="scripture-text">...</div> and convert to <p>...</p>
    content = content.replace(/<div class="scripture-text">([^<]*(?:<(?!\/div>)[^<]*)*)<\/div>/gi,
        '<p class="scripture-text">$1</p>');
    content = content.replace(/<div class="scripture-ref">([^<]*(?:<(?!\/div>)[^<]*)*)<\/div>/gi,
        '<p class="scripture-ref">$1</p>');

    return content
        // Remove aria attributes (handled by reveal.js)
        .replace(/\s*aria-[a-z]+="[^"]*"/gi, '')
        .replace(/\s*role="[^"]*"/gi, '')
        .replace(/\s*id="s\d+-title"/gi, '')
        // Convert content-list
        .replace(/<div class="content-list"><ul>/gi, '<ul>')
        .replace(/<\/ul><\/div>/gi, '</ul>')
        // Convert list wrapper to just ul
        .replace(/<div class="list">\s*<ul>/gi, '<ul>')
        // Add fragments to list items (only top level, not nested)
        .replace(/<li>(?!<li)/gi, '<li class="fragment fade-up">')
        // Convert panel to scripture (for Marriage Series)
        .replace(/<div class="panel"[^>]*>/gi, '<div class="scripture">')
        // Convert .ref to scripture-ref
        .replace(/<p class="ref">/gi, '<p class="scripture-ref">')
        // Convert call-to-action
        .replace(/<div class="call-to-action">/gi, '<div class="cta">')
        // Convert two-column
        .replace(/<div class="two-column">/gi, '<div class="two-columns">')
        // Clean up prayer points wrapper
        .replace(/<div class="prayer-points"><div class="content-list">/gi, '<div class="prayer-points">')
        .replace(/<\/ul><\/div><\/div>/gi, '</ul></div>');
}

// Generate reveal.js HTML
function generateRevealHTML(title, slides, isMonthlyPrayer = false) {
    const cssPath = isMonthlyPrayer ? '../../css/theme-prayer.css' : '../css/theme-prayer.css';
    const homePath = isMonthlyPrayer ? '../../index.html' : '../index.html';

    const slidesHTML = slides.map((slide, idx) => {
        const attrs = idx === 0
            ? ' data-auto-animate data-background-gradient="radial-gradient(ellipse at center, #1b263b 0%, #0d1b2a 100%)"'
            : '';
        return `
            <section${attrs}>
${cleanContent(slide.content)}
            </section>`;
    }).join('\n');

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="${title} - Prayer Presentation">
    <title>${title} - Prayer Presentation</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
    <link rel="stylesheet" href="${cssPath}">
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
        <div class="slides">${slidesHTML}
        </div>
    </div>

    <!-- Slide Navigator Trigger Button -->
    <button class="slide-nav-trigger" aria-label="Open slide navigator" title="View all slides">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
    </button>

    <!-- Slide Navigator Modal -->
    <div class="slide-nav-modal" id="slideNavModal" role="dialog" aria-label="Slide navigator" aria-modal="true">
        <div class="slide-nav-header">
            <div>
                <h2>Slide Navigator</h2>
                <span class="slide-count" id="slideNavCount"></span>
            </div>
            <button class="slide-nav-close" aria-label="Close navigator">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        </div>
        <div class="slide-nav-content">
            <div class="slide-nav-grid" id="slideNavGrid"></div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
    <script>
        // Responsive dimensions based on screen size
        const isMobile = window.innerWidth <= 768;
        const isSmallPhone = window.innerWidth <= 480;

        Reveal.initialize({
            width: isSmallPhone ? 375 : (isMobile ? 768 : 1920),
            height: isSmallPhone ? 667 : (isMobile ? 1024 : 1080),
            margin: isSmallPhone ? 0.02 : (isMobile ? 0.05 : 0.04),
            minScale: 0.1, maxScale: 2.0,
            hash: true, history: true, hashOneBasedIndex: true,
            controls: true, controlsTutorial: false,
            controlsLayout: 'bottom-right', controlsBackArrows: 'faded',
            progress: true, slideNumber: isMobile ? false : 'c/t', showSlideNumber: 'all',
            transition: isMobile ? 'none' : 'slide', transitionSpeed: 'fast',
            backgroundTransition: 'none',
            autoAnimate: !isMobile, autoAnimateDuration: 0.5,
            fragments: true, fragmentInURL: false,
            keyboard: true, touch: true, center: true,
            embedded: false, help: true, pause: true,
            hideInactiveCursor: true, hideCursorTime: 3000,
            disableLayout: false,
            pdfSeparateFragments: false, pdfMaxPagesPerSlide: 1,
        });
        Reveal.addKeyBinding({ keyCode: 72, key: 'H' }, () => {
            window.location.href = '${homePath}';
        });
        if (new URLSearchParams(window.location.search).get('overview') === 'true') {
            Reveal.addEventListener('ready', () => Reveal.toggleOverview(true));
        }

        // Slide Navigator functionality
        (function() {
            const modal = document.getElementById('slideNavModal');
            const grid = document.getElementById('slideNavGrid');
            const countEl = document.getElementById('slideNavCount');
            const trigger = document.querySelector('.slide-nav-trigger');
            const closeBtn = document.querySelector('.slide-nav-close');

            function getSlideType(section) {
                const text = section.textContent.toLowerCase();
                const html = section.innerHTML.toLowerCase();
                if (section.querySelector('h1') && !section.querySelector('h2')) return 'title';
                if (html.includes('prayer') || html.includes('lord,') || html.includes('father,')) return 'prayer';
                if (section.querySelector('.scripture') || html.includes('scripture')) return 'scripture';
                return 'content';
            }

            function getSlideTitle(section, index) {
                const h1 = section.querySelector('h1');
                const h2 = section.querySelector('h2');
                const h3 = section.querySelector('h3');
                if (h1) return h1.textContent.trim().substring(0, 40);
                if (h2) return h2.textContent.trim().substring(0, 40);
                if (h3) return h3.textContent.trim().substring(0, 40);
                return 'Slide ' + (index + 1);
            }

            function getSlidePreview(section) {
                const h1 = section.querySelector('h1');
                const h2 = section.querySelector('h2');
                const p = section.querySelector('p');
                const scripture = section.querySelector('.scripture-text');
                let text = '';
                if (h1) text += h1.textContent.trim() + ' ';
                if (h2) text += h2.textContent.trim() + ' ';
                if (scripture) text += scripture.textContent.trim().substring(0, 80);
                else if (p) text += p.textContent.trim().substring(0, 80);
                return text.trim() || 'Slide content';
            }

            function buildNavGrid() {
                const slides = document.querySelectorAll('.reveal .slides > section');
                const total = slides.length;
                const current = Reveal.getIndices().h;
                countEl.textContent = total + ' slides';
                grid.innerHTML = '';

                slides.forEach((section, index) => {
                    const type = getSlideType(section);
                    const title = getSlideTitle(section, index);
                    const preview = getSlidePreview(section);
                    const isActive = index === current;

                    const card = document.createElement('div');
                    card.className = 'slide-nav-card' + (isActive ? ' active' : '');
                    card.dataset.type = type;
                    card.dataset.index = index;
                    card.setAttribute('role', 'button');
                    card.setAttribute('tabindex', '0');
                    card.setAttribute('aria-label', 'Go to slide ' + (index + 1) + ': ' + title);

                    card.innerHTML = \`
                        <div class="slide-nav-preview">
                            <span class="preview-text">\${preview}</span>
                        </div>
                        <div class="slide-nav-info">
                            <span class="slide-nav-number">\${index + 1}</span>
                            <span class="slide-nav-title">\${title}</span>
                        </div>
                    \`;

                    card.addEventListener('click', () => goToSlide(index));
                    card.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            goToSlide(index);
                        }
                    });

                    grid.appendChild(card);
                });
            }

            function goToSlide(index) {
                Reveal.slide(index);
                closeModal();
            }

            function openModal() {
                buildNavGrid();
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
                closeBtn.focus();
                // Scroll to active slide
                setTimeout(() => {
                    const activeCard = grid.querySelector('.slide-nav-card.active');
                    if (activeCard) {
                        activeCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 100);
            }

            function closeModal() {
                modal.classList.remove('active');
                document.body.style.overflow = '';
                trigger.focus();
            }

            // Event listeners
            trigger.addEventListener('click', openModal);
            closeBtn.addEventListener('click', closeModal);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal();
            });
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && modal.classList.contains('active')) {
                    closeModal();
                }
                // 'G' key to open navigator
                if (e.key === 'g' || e.key === 'G') {
                    if (!modal.classList.contains('active')) {
                        e.preventDefault();
                        openModal();
                    }
                }
            });

            // Update active state on slide change
            Reveal.on('slidechanged', () => {
                if (modal.classList.contains('active')) {
                    const current = Reveal.getIndices().h;
                    grid.querySelectorAll('.slide-nav-card').forEach((card, idx) => {
                        card.classList.toggle('active', idx === current);
                    });
                }
            });
        })();
    </script>
</body>
</html>`;
}

// Extract date from filename or use file modification time
function extractDate(filename, sourcePath) {
    const months = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    };

    const lowerName = filename.toLowerCase();

    // Try to extract date from filename (e.g., January_2026, December_2025)
    for (const [month, num] of Object.entries(months)) {
        if (lowerName.includes(month)) {
            const yearMatch = lowerName.match(/20\d{2}/);
            if (yearMatch) {
                return `${yearMatch[0]}-${num}-01`;
            }
        }
    }

    // Check for year patterns like 2025, 2026 in filename
    const yearMatch = lowerName.match(/20(2[4-9])/);
    if (yearMatch) {
        return `${yearMatch[0]}-01-01`;
    }

    // Fall back to file modification time
    try {
        const stats = fs.statSync(sourcePath);
        return stats.mtime.toISOString().split('T')[0];
    } catch {
        return '2024-01-01';
    }
}

// Convert a single file
function convertFile(sourcePath, targetPath, isMonthlyPrayer = false) {
    try {
        const html = fs.readFileSync(sourcePath, 'utf8');
        const { title, speaker } = extractMetadata(html);
        const slides = parseSlides(html);

        if (slides.length === 0) {
            console.log(`  Skipping ${path.basename(sourcePath)} - no slides found`);
            return null;
        }

        const output = generateRevealHTML(title, slides, isMonthlyPrayer);
        fs.writeFileSync(targetPath, output, 'utf8');

        const filename = path.basename(sourcePath);
        const date = extractDate(filename, sourcePath);

        console.log(`  Converted: ${filename} (${slides.length} slides, ${date})`);

        const category = sourcePath.includes('monthly_prayer') ? 'prayer' :
                      (sourcePath.toLowerCase().includes('prayer') ? 'prayer' : 'sermon');
        const tags = generateTags(title, category, isMonthlyPrayer);

        return {
            title,
            speaker,
            slides: slides.length,
            file: path.relative(path.join(__dirname, '..', 'site', 'modern'), targetPath),
            id: path.basename(sourcePath, '.html').toLowerCase().replace(/_/g, '-'),
            category,
            tags,
            featured: false,
            date
        };
    } catch (err) {
        console.error(`  Error: ${path.basename(sourcePath)} - ${err.message}`);
        return null;
    }
}

// Main
function main() {
    console.log('Converting presentations to Reveal.js (v2)...\n');

    const presentations = [];
    let converted = 0;
    let skipped = 0;

    // Process main presentations
    console.log('Sermon presentations:');
    const mainFiles = fs.readdirSync(SOURCE_DIR).filter(f => f.endsWith('.html'));

    for (const file of mainFiles) {
        // Skip already manually converted
        if (file === 'Have_I_Not_Called_You_Presentation.html') {
            console.log(`  Skipping ${file} - already converted manually`);
            skipped++;
            continue;
        }

        const sourcePath = path.join(SOURCE_DIR, file);
        const targetFile = file.replace('_Presentation', '').replace('.html', '.html');
        const targetPath = path.join(TARGET_DIR, targetFile);

        const result = convertFile(sourcePath, targetPath, false);
        if (result) {
            presentations.push(result);
            converted++;
        } else {
            skipped++;
        }
    }

    // Process monthly prayers
    console.log('\nMonthly prayer presentations:');
    if (fs.existsSync(MONTHLY_PRAYER_SOURCE)) {
        const monthlyFiles = fs.readdirSync(MONTHLY_PRAYER_SOURCE).filter(f => f.endsWith('.html'));

        for (const file of monthlyFiles) {
            const sourcePath = path.join(MONTHLY_PRAYER_SOURCE, file);
            const targetPath = path.join(MONTHLY_PRAYER_TARGET, file);

            const result = convertFile(sourcePath, targetPath, true);
            if (result) {
                result.file = 'presentations/monthly_prayer/' + file;
                presentations.push(result);
                converted++;
            } else {
                skipped++;
            }
        }
    }

    // Save presentations data
    const dataPath = path.join(__dirname, '..', 'site', 'modern', 'presentations-data.js');
    fs.writeFileSync(dataPath, `const presentations = ${JSON.stringify(presentations, null, 2)};\n`);

    console.log(`\n${'='.repeat(50)}`);
    console.log(`Converted: ${converted}`);
    console.log(`Skipped: ${skipped}`);
    console.log(`Total: ${presentations.length}`);
}

main();
