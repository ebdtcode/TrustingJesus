#!/usr/bin/env node
/**
 * Convert Modern Presentations to V2 Stained Glass Theme
 *
 * This script converts presentations from the modern folder to the v2
 * stained glass theme, updating:
 * - CSS links
 * - Home button links
 * - Font imports
 * - Slide navigator
 * - Reveal.js configuration
 */

const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
    modernDir: path.join(__dirname, '../../modern/presentations'),
    v2Dir: path.join(__dirname, '../presentations'),
    dataFile: path.join(__dirname, '../data/presentations.js')
};

// Category mapping based on presentations.js
const categoryFolders = {
    'family': 'family',
    'prayer': 'prayer',
    'faith': 'faith',
    'grace': 'grace',
    'sermon': 'sermons',
    'marriage': 'marriage',
    'names-of-god': 'names-of-god',
    'series': 'series'
};

// Load presentations data
function loadPresentationsData() {
    try {
        const content = fs.readFileSync(CONFIG.dataFile, 'utf8');
        // Extract the presentations array using regex
        const match = content.match(/const presentations = \[([\s\S]*?)\];/);
        if (!match) {
            console.error('Could not find presentations array in data file');
            return [];
        }

        // Parse the array (convert to proper JSON format)
        let arrayStr = '[' + match[1] + ']';
        // Convert JavaScript object literals to JSON
        arrayStr = arrayStr
            .replace(/(\w+):/g, '"$1":') // Quote property names
            .replace(/'/g, '"') // Convert single quotes to double
            .replace(/,\s*}/g, '}') // Remove trailing commas
            .replace(/,\s*]/g, ']'); // Remove trailing commas in arrays

        return JSON.parse(arrayStr);
    } catch (err) {
        console.error('Error loading presentations data:', err.message);
        return [];
    }
}

// Get the modern file path from the presentations data entry
function getModernFilePath(entry) {
    const file = entry.file;
    if (!file) return null;

    // Handle different path formats
    if (file.startsWith('presentations/')) {
        // Already a v2 path
        return path.join(CONFIG.modernDir, '..', 'v2', file);
    } else if (file.startsWith('../modern/')) {
        return path.join(CONFIG.v2Dir, '..', file);
    } else if (file.startsWith('../growth/')) {
        // Skip growth folder presentations
        return null;
    }

    return null;
}

// Determine the v2 folder for a presentation
function getV2Folder(category) {
    return categoryFolders[category] || 'sermons';
}

// Calculate relative path depth for a file in v2
function getRelativePathToRoot(category) {
    // All presentations are one level deep: /v2/presentations/{category}/file.html
    return '../..';
}

// Convert a single presentation file
function convertPresentation(sourcePath, destPath, category) {
    try {
        let content = fs.readFileSync(sourcePath, 'utf8');
        const relPath = getRelativePathToRoot(category);

        // Skip if already converted (has v2 theme reference)
        if (content.includes('presentation-theme.css') || content.includes('Stained Glass')) {
            console.log(`  Skipping (already v2): ${path.basename(sourcePath)}`);
            return false;
        }

        // 1. Replace CSS links
        content = content.replace(
            /<link rel="stylesheet" href="[^"]*theme-prayer\.css">/g,
            `<link rel="stylesheet" href="${relPath}/assets/css/presentation-theme.css">`
        );

        // 2. Add Google Fonts if not present
        if (!content.includes('fonts.googleapis.com')) {
            const fontLinks = `
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">
`;
            // Insert after reveal.css
            content = content.replace(
                /(<link rel="stylesheet" href="[^"]*reveal\.css">)/,
                '$1' + fontLinks
            );
        }

        // 3. Update home button link to v2 presentations page
        content = content.replace(
            /<a href="[^"]*" class="home-btn"/g,
            `<a href="${relPath}/presentations.html" class="home-btn"`
        );

        // 4. Remove old skip-link styles (now in theme CSS)
        content = content.replace(
            /<style>\s*\.skip-link\s*\{[^}]*\}\s*\.skip-link:focus\s*\{[^}]*\}\s*<\/style>/gs,
            ''
        );
        content = content.replace(
            /<style>\s*\/\* Skip link[^<]*<\/style>/gs,
            ''
        );

        // 5. Add v2 presentation JS before closing body tag if not present
        if (!content.includes('presentation.js')) {
            content = content.replace(
                /<\/body>/,
                `    <script src="${relPath}/assets/js/presentation.js"></script>\n</body>`
            );
        }

        // 6. Update Reveal.js initialization to use v2 settings
        content = content.replace(
            /Reveal\.initialize\(\{[\s\S]*?\}\);/,
            `Reveal.initialize({
            width: 960,
            height: 700,
            margin: 0.1,
            minScale: 0.2,
            maxScale: 2.0,
            hash: true,
            history: true,
            hashOneBasedIndex: true,
            navigationMode: 'linear',
            controls: true,
            controlsTutorial: true,
            progress: true,
            slideNumber: 'c/t',
            showSlideNumber: 'all',
            transition: 'fade',
            transitionSpeed: 'default',
            backgroundTransition: 'fade',
            autoAnimate: true,
            autoAnimateDuration: 0.6,
            fragments: true,
            fragmentInURL: true,
            keyboard: true,
            touch: true,
            center: true,
            help: true,
        });

        // Add H key to go home
        Reveal.addKeyBinding({ keyCode: 72, key: 'H', description: 'Go home' }, () => {
            window.location.href = '${relPath}/presentations.html';
        });`
        );

        // 7. Update background gradients to v2 style
        content = content.replace(
            /data-background-gradient="radial-gradient\(ellipse at center, #1b263b 0%, #0d1b2a 100%\)"/g,
            'data-background-gradient="radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a12 100%)"'
        );

        // 8. Convert .scripture to .scripture-glass
        content = content.replace(/<div class="scripture">/g, '<div class="scripture-glass">');
        content = content.replace(/<div class="scripture" /g, '<div class="scripture-glass" ');

        // 9. Add slide navigator trigger and modal if not present
        if (!content.includes('slide-nav-trigger')) {
            const slideNav = `
    <!-- Slide Navigator Trigger -->
    <button class="slide-nav-trigger" aria-label="Open slide navigator" title="View all slides (G)">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
    </button>

    <!-- Slide Navigator Modal -->
    <div class="slide-nav-modal" id="slideNavModal" role="dialog" aria-label="Slide navigator" aria-modal="true" aria-hidden="true">
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

`;
            // Insert before the reveal div
            content = content.replace(
                /(<div class="reveal")/,
                slideNav + '    $1'
            );
        }

        // Write converted file
        fs.mkdirSync(path.dirname(destPath), { recursive: true });
        fs.writeFileSync(destPath, content, 'utf8');
        return true;
    } catch (err) {
        console.error(`  Error converting ${path.basename(sourcePath)}: ${err.message}`);
        return false;
    }
}

// Process all presentations
function processAll() {
    console.log('Converting presentations to v2 theme...\n');

    // Get all HTML files from modern folder
    const modernFiles = [];

    function scanDir(dir, subpath = '') {
        const items = fs.readdirSync(dir);
        for (const item of items) {
            const fullPath = path.join(dir, item);
            const relPath = subpath ? path.join(subpath, item) : item;
            const stat = fs.statSync(fullPath);

            if (stat.isDirectory()) {
                scanDir(fullPath, relPath);
            } else if (item.endsWith('.html')) {
                modernFiles.push({ path: fullPath, relPath });
            }
        }
    }

    scanDir(CONFIG.modernDir);

    console.log(`Found ${modernFiles.length} presentation files\n`);

    // Map files to categories based on presentations.js
    const presentations = loadPresentationsData();
    const fileToCategory = new Map();

    for (const p of presentations) {
        if (!p.file) continue;
        const fileName = path.basename(p.file.replace('../modern/presentations/', '').replace('monthly_prayer/', ''));
        fileToCategory.set(fileName, p.category || 'sermon');
    }

    // Convert each file
    let converted = 0;
    let skipped = 0;
    let errors = 0;

    for (const { path: sourcePath, relPath } of modernFiles) {
        const fileName = path.basename(sourcePath);
        const dirName = path.dirname(relPath);

        // Determine category
        let category = fileToCategory.get(fileName);
        if (!category) {
            // Infer from directory
            if (dirName === 'monthly_prayer') {
                category = 'prayer';
            } else if (dirName === 'family') {
                category = 'family';
            } else {
                category = 'sermon';
            }
        }

        const folder = getV2Folder(category);
        const destPath = path.join(CONFIG.v2Dir, folder, fileName);

        console.log(`Processing: ${relPath}`);
        console.log(`  Category: ${category} -> ${folder}`);
        console.log(`  Destination: presentations/${folder}/${fileName}`);

        const result = convertPresentation(sourcePath, destPath, category);
        if (result === true) {
            converted++;
            console.log('  Status: Converted');
        } else if (result === false) {
            skipped++;
        } else {
            errors++;
        }
        console.log('');
    }

    console.log('\n=== Summary ===');
    console.log(`Converted: ${converted}`);
    console.log(`Skipped: ${skipped}`);
    console.log(`Errors: ${errors}`);
    console.log(`Total: ${modernFiles.length}`);
}

// Run
processAll();
