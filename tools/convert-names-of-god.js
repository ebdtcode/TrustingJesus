#!/usr/bin/env node
/**
 * Converts Names of God reference document to Reveal.js slides
 * Groups names by section and creates multiple slides per section
 */

const fs = require('fs');
const path = require('path');

const SOURCE_FILE = path.join(__dirname, '..', 'site', 'presentations', 'Names_of_God_Presentation.html');
const TARGET_FILE = path.join(__dirname, '..', 'site', 'modern', 'presentations', 'Names_of_God.html');

// Read source file
const html = fs.readFileSync(SOURCE_FILE, 'utf8');

// Extract sections and their content
function extractSections(html) {
    const sections = [];

    // Match section titles
    const sectionRegex = /<section id="([^"]+)">\s*<h2 class="section-title"[^>]*>([^<]+)<\/h2>/gi;
    let match;

    while ((match = sectionRegex.exec(html)) !== null) {
        const sectionId = match[1];
        const sectionTitle = match[2].trim();
        const startIdx = match.index;

        // Find next section or end
        const nextSection = html.indexOf('<section id="', startIdx + 1);
        const endIdx = nextSection > 0 ? nextSection : html.indexOf('</main>', startIdx);

        const content = html.substring(startIdx, endIdx);

        // Extract name cards
        const cards = [];
        const cardRegex = /<div class="name-card(?:\s+featured)?">([\s\S]*?)<\/div>\s*(?=<div class="name-card|<\/div>\s*<\/section|<section|$)/gi;
        let cardMatch;

        while ((cardMatch = cardRegex.exec(content)) !== null) {
            const cardHtml = cardMatch[1];

            const hebrewMatch = cardHtml.match(/<div class="hebrew-name">([^<]+)<\/div>/);
            const pronMatch = cardHtml.match(/<div class="pronunciation">([^<]+)<\/div>/);
            const englishMatch = cardHtml.match(/<div class="english-name">([^<]+)<\/div>/);
            const meaningMatch = cardHtml.match(/<div class="meaning">([\s\S]*?)<\/div>/);
            const scriptureTextMatch = cardHtml.match(/<div class="scripture-text">([^<]+)<\/div>/);
            const scriptureRefMatch = cardHtml.match(/<span class="scripture-ref">([^<]+)<\/span>|<a[^>]*class="scripture-ref"[^>]*>([^<]+)<\/a>/);

            cards.push({
                hebrewName: hebrewMatch ? hebrewMatch[1].trim() : '',
                pronunciation: pronMatch ? pronMatch[1].trim() : '',
                englishName: englishMatch ? englishMatch[1].trim() : '',
                meaning: meaningMatch ? meaningMatch[1].trim().replace(/\s+/g, ' ') : '',
                scriptureText: scriptureTextMatch ? scriptureTextMatch[1].trim() : '',
                scriptureRef: scriptureRefMatch ? (scriptureRefMatch[1] || scriptureRefMatch[2]).trim() : ''
            });
        }

        // Extract name items (simpler format)
        const items = [];
        const itemRegex = /<div class="name-item">([\s\S]*?)<\/div>\s*(?=<div class="name-item|<\/div>\s*<\/section|<section|$)/gi;
        let itemMatch;

        while ((itemMatch = itemRegex.exec(content)) !== null) {
            const itemHtml = itemMatch[1];

            const nameMatch = itemHtml.match(/<div class="name">([^<]+)<\/div>/);
            const descMatch = itemHtml.match(/<div class="desc">([^<]+)<\/div>/);
            const refMatch = itemHtml.match(/<div class="ref">(?:<a[^>]*>)?([^<]+)(?:<\/a>)?<\/div>/);

            if (nameMatch) {
                items.push({
                    name: nameMatch ? nameMatch[1].trim() : '',
                    desc: descMatch ? descMatch[1].trim() : '',
                    ref: refMatch ? refMatch[1].trim() : ''
                });
            }
        }

        if (cards.length > 0 || items.length > 0) {
            sections.push({
                id: sectionId,
                title: sectionTitle,
                cards,
                items
            });
        }
    }

    return sections;
}

// Extract prayer points
function extractPrayer(html) {
    const prayerMatch = html.match(/<section[^>]*id="prayer"[^>]*>([\s\S]*?)<\/section>/i);
    if (!prayerMatch) return [];

    const points = [];
    const pointRegex = /<div class="prayer-point">\s*<p>([^<]+)<\/p>/gi;
    let match;

    while ((match = pointRegex.exec(prayerMatch[1])) !== null) {
        points.push(match[1].trim());
    }

    return points;
}

// Extract closing
function extractClosing(html) {
    const closingMatch = html.match(/<section[^>]*id="closing"[^>]*class="closing"[^>]*>([\s\S]*?)<\/section>/i);
    if (!closingMatch) {
        const altMatch = html.match(/<div class="closing"[^>]*>([\s\S]*?)<\/div>/i);
        if (!altMatch) return { title: '', text: '' };

        const titleMatch = altMatch[1].match(/<h3>([^<]+)<\/h3>/);
        const textMatch = altMatch[1].match(/<p>([^<]+)<\/p>/);

        return {
            title: titleMatch ? titleMatch[1].trim() : '',
            text: textMatch ? textMatch[1].trim() : ''
        };
    }

    const titleMatch = closingMatch[1].match(/<h3>([^<]+)<\/h3>/);
    const textMatch = closingMatch[1].match(/<p>([^<]+)<\/p>/);

    return {
        title: titleMatch ? titleMatch[1].trim() : '',
        text: textMatch ? textMatch[1].trim() : ''
    };
}

// Generate slides HTML
function generateSlides(sections, prayerPoints, closing) {
    let slides = [];

    // Title slide
    slides.push(`
            <section data-auto-animate data-background-gradient="radial-gradient(ellipse at center, #1b263b 0%, #0d1b2a 100%)">
                <h1>The Names of God</h1>
                <h2>And Their Meaning</h2>
                <div class="cta">
                    <h3>150+ Biblical Names with Scripture References</h3>
                </div>
                <p class="subtitle">
                    Throughout Scripture, God reveals Himself through His names.
                </p>
            </section>`);

    // Overview slide
    slides.push(`
            <section>
                <h2>What We Will Explore</h2>
                <div class="two-columns">
                    <div class="column">
                        <h4>Hebrew Names</h4>
                        <ul>
                            <li class="fragment fade-up">Primary Names (11)</li>
                            <li class="fragment fade-up">El Compounds (21)</li>
                            <li class="fragment fade-up">Yahweh Compounds (17)</li>
                        </ul>
                    </div>
                    <div class="column">
                        <h4>New Testament</h4>
                        <ul>
                            <li class="fragment fade-up">Names of Jesus (20)</li>
                            <li class="fragment fade-up">I AM Statements (7)</li>
                            <li class="fragment fade-up">Divine Titles (110+)</li>
                        </ul>
                    </div>
                </div>
            </section>`);

    // Process each section
    for (const section of sections) {
        // Section title slide
        slides.push(`
            <section>
                <h2>${section.title}</h2>
                <p class="subtitle">${section.cards.length + section.items.length} Names in this section</p>
            </section>`);

        // Featured cards (2 per slide)
        if (section.cards.length > 0) {
            for (let i = 0; i < section.cards.length; i += 2) {
                const cardsOnSlide = section.cards.slice(i, i + 2);

                if (cardsOnSlide.length === 2) {
                    slides.push(`
            <section>
                <h2>${section.title}</h2>
                <div class="two-columns">
                    ${cardsOnSlide.map(card => `
                    <div class="scripture">
                        <h4>${card.hebrewName}</h4>
                        ${card.pronunciation ? `<p class="subtitle"><em>Pronounced: ${card.pronunciation}</em></p>` : ''}
                        ${card.englishName ? `<p class="subtitle"><em>${card.englishName}</em></p>` : ''}
                        <p>${card.meaning.substring(0, 180)}${card.meaning.length > 180 ? '...' : ''}</p>
                        ${card.scriptureRef ? `<p class="scripture-ref">${card.scriptureRef}</p>` : ''}
                    </div>`).join('')}
                </div>
            </section>`);
                } else {
                    // Single card slide
                    const card = cardsOnSlide[0];
                    slides.push(`
            <section>
                <h2>${section.title}</h2>
                <div class="scripture">
                    <h4>${card.hebrewName}</h4>
                    ${card.pronunciation ? `<p class="subtitle"><em>Pronounced: ${card.pronunciation}</em></p>` : ''}
                    ${card.englishName ? `<p class="subtitle"><em>${card.englishName}</em></p>` : ''}
                    <p>${card.meaning}</p>
                    ${card.scriptureText ? `<div class="quote">"${card.scriptureText}"</div>` : ''}
                    ${card.scriptureRef ? `<p class="scripture-ref">${card.scriptureRef}</p>` : ''}
                </div>
            </section>`);
                }
            }
        }

        // Name items (4 per slide for better mobile readability)
        if (section.items.length > 0) {
            for (let i = 0; i < section.items.length; i += 4) {
                const itemsOnSlide = section.items.slice(i, i + 4);

                slides.push(`
            <section>
                <h2>${section.title}</h2>
                <div class="prayer-points">
                    <ul>
                        ${itemsOnSlide.map(item => `
                        <li class="fragment fade-up">
                            <strong>${item.name}</strong> - ${item.desc}
                            ${item.ref ? `<span class="scripture-ref">${item.ref}</span>` : ''}
                        </li>`).join('')}
                    </ul>
                </div>
            </section>`);
            }
        }
    }

    // Prayer slides
    if (prayerPoints.length > 0) {
        slides.push(`
            <section>
                <h2>Prayer Focus</h2>
                <p class="subtitle">Using God's Names in Prayer</p>
            </section>`);

        for (let i = 0; i < prayerPoints.length; i += 2) {
            const pointsOnSlide = prayerPoints.slice(i, i + 2);
            slides.push(`
            <section>
                <h2>Prayer Points</h2>
                <div class="prayer-points">
                    <ul>
                        ${pointsOnSlide.map(point => `
                        <li class="fragment fade-up">${point}</li>`).join('')}
                    </ul>
                </div>
            </section>`);
        }
    }

    // Closing slide
    if (closing.title || closing.text) {
        slides.push(`
            <section>
                <div class="cta">
                    <h3>${closing.title || 'Know Him by Name'}</h3>
                    <p>${closing.text || 'May these names draw you closer to the One who calls you by name.'}</p>
                </div>
            </section>`);
    }

    return slides;
}

// Generate full HTML
function generateHTML(slides) {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="The Names of God - 150+ Biblical Names Study Resource">
    <title>The Names of God - Prayer Presentation</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
    <link rel="stylesheet" href="../css/theme-prayer.css">
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
    <a href="../index.html" class="home-btn" aria-label="Return to presentations list">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span>Home</span>
    </a>

    <div class="reveal" id="main-content">
        <div class="slides">${slides.join('\n')}
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
            window.location.href = '../index.html';
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
                const h4 = section.querySelector('h4');
                if (h1) return h1.textContent.trim().substring(0, 40);
                if (h2) return h2.textContent.trim().substring(0, 40);
                if (h3) return h3.textContent.trim().substring(0, 40);
                if (h4) return h4.textContent.trim().substring(0, 40);
                return 'Slide ' + (index + 1);
            }

            function getSlidePreview(section) {
                const h1 = section.querySelector('h1');
                const h2 = section.querySelector('h2');
                const h4 = section.querySelector('h4');
                const p = section.querySelector('p');
                let text = '';
                if (h1) text += h1.textContent.trim() + ' ';
                if (h2) text += h2.textContent.trim() + ' ';
                if (h4) text += h4.textContent.trim() + ' ';
                else if (p) text += p.textContent.trim().substring(0, 80);
                return text.trim() || 'Slide content';
            }

            function buildNavGrid() {
                // Use Reveal.js API for reliable slide detection on all devices
                const slides = Reveal.getSlides();
                const total = Reveal.getTotalSlides();
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

            trigger.addEventListener('click', openModal);
            closeBtn.addEventListener('click', closeModal);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal();
            });
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && modal.classList.contains('active')) {
                    closeModal();
                }
                if (e.key === 'g' || e.key === 'G') {
                    if (!modal.classList.contains('active')) {
                        e.preventDefault();
                        openModal();
                    }
                }
            });

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

// Main
console.log('Converting Names of God to Reveal.js...\n');

const sections = extractSections(html);
console.log(`Found ${sections.length} sections`);
sections.forEach(s => console.log(`  - ${s.title}: ${s.cards.length} cards, ${s.items.length} items`));

const prayerPoints = extractPrayer(html);
console.log(`Found ${prayerPoints.length} prayer points`);

const closing = extractClosing(html);
console.log(`Closing: "${closing.title}"`);

const slides = generateSlides(sections, prayerPoints, closing);
console.log(`\nGenerated ${slides.length} slides`);

const output = generateHTML(slides);
fs.writeFileSync(TARGET_FILE, output, 'utf8');
console.log(`\nSaved to: ${TARGET_FILE}`);

// Update presentations-data.js
const dataPath = path.join(__dirname, '..', 'site', 'modern', 'presentations-data.js');
const dataContent = fs.readFileSync(dataPath, 'utf8');
const presentations = eval(dataContent.replace('const presentations = ', '').replace(/;\s*$/, ''));

// Check if already exists
const existingIdx = presentations.findIndex(p => p.id === 'names-of-god');
const newEntry = {
    title: 'The Names of God',
    speaker: '',
    slides: slides.length,
    file: 'presentations/Names_of_God.html',
    id: 'names-of-god',
    category: 'sermon',
    tags: ['names', 'god', 'hebrew', 'greek', 'elohim', 'yahweh', 'adonai', 'jehovah', 'jesus', 'i am', 'study', 'reference', 'biblical names', '150+ names'],
    featured: true,
    description: '150+ Biblical Names with Scripture References - A comprehensive study of Hebrew names, compound names, and New Testament names of Jesus.',
    date: '2099-12-31'  // Always show first (featured resource)
};

if (existingIdx >= 0) {
    presentations[existingIdx] = newEntry;
} else {
    // Add at the beginning since it's featured
    presentations.unshift(newEntry);
}

fs.writeFileSync(dataPath, `const presentations = ${JSON.stringify(presentations, null, 2)};\n`);
console.log('Updated presentations-data.js');
