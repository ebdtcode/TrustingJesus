#!/usr/bin/env node
/**
 * Fix V2 Presentations
 *
 * This script fixes common issues in converted presentations:
 * 1. Removes duplicate home buttons (emoji-based ones inside slides)
 * 2. Removes inline navigator JavaScript (replaced by shared presentation.js)
 * 3. Ensures presentation.js is loaded before Reveal.initialize()
 */

const fs = require('fs');
const path = require('path');

const presentationsDir = path.join(__dirname, '..', 'presentations');

function fixPresentation(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    let modified = false;

    // Remove duplicate home button (emoji version inside slides)
    const duplicateHomeRegex = /\s*<!-- Home Button -->\s*\n\s*<a href="[^"]*" class="home-btn">\s*\n\s*<span>[🏠]<\/span>\s*\n\s*<span>Home<\/span>\s*\n\s*<\/a>/g;
    if (duplicateHomeRegex.test(content)) {
        content = content.replace(duplicateHomeRegex, '');
        modified = true;
        console.log(`  - Removed duplicate home button`);
    }

    // Remove nav buttons if inside last section
    const navButtonsRegex = /\s*<!-- Navigation -->\s*\n\s*<nav class="nav">\s*\n\s*<button[^>]*>← Previous<\/button>\s*\n\s*<button[^>]*>Next →<\/button>\s*\n\s*<\/nav>/g;
    if (navButtonsRegex.test(content)) {
        content = content.replace(navButtonsRegex, '');
        modified = true;
        console.log(`  - Removed redundant nav buttons`);
    }

    // Remove inline navigator JavaScript (the large IIFE)
    // Pattern: (function() { ... with slide-nav-card ... })();
    const inlineNavRegex = /\s*\/\/ Slide Navigator functionality\s*\n\s*\(function\(\)\s*\{[\s\S]*?slide-nav-card[\s\S]*?\}\)\(\);/g;
    if (inlineNavRegex.test(content)) {
        content = content.replace(inlineNavRegex, '');
        modified = true;
        console.log(`  - Removed inline navigator code`);
    }

    // Remove duplicate H key bindings (keep only one)
    const duplicateHKeyRegex = /\s*Reveal\.addKeyBinding\(\s*\{\s*keyCode:\s*72,\s*key:\s*'H'\s*\}\s*,\s*\(\)\s*=>\s*\{\s*\n\s*window\.location\.href\s*=\s*'\.\.\/index\.html';\s*\n\s*\}\);/g;
    if (duplicateHKeyRegex.test(content)) {
        content = content.replace(duplicateHKeyRegex, '');
        modified = true;
        console.log(`  - Removed duplicate H key binding`);
    }

    // Remove overview query param check
    const overviewCheckRegex = /\s*if\s*\(new URLSearchParams\(window\.location\.search\)\.get\('overview'\)\s*===\s*'true'\)\s*\{\s*\n\s*Reveal\.addEventListener\('ready',\s*\(\)\s*=>\s*Reveal\.toggleOverview\(true\)\);\s*\n\s*\}/g;
    if (overviewCheckRegex.test(content)) {
        content = content.replace(overviewCheckRegex, '');
        modified = true;
        console.log(`  - Removed overview query param check`);
    }

    // Remove mobile variables
    const mobileVarsRegex = /\s*\/\/ Responsive dimensions based on screen size\s*\n\s*const isMobile = window\.innerWidth <= 768;\s*\n\s*const isSmallPhone = window\.innerWidth <= 480;\s*\n/g;
    if (mobileVarsRegex.test(content)) {
        content = content.replace(mobileVarsRegex, '\n');
        modified = true;
        console.log(`  - Removed unused mobile variables`);
    }

    // Ensure presentation.js is loaded before the script block
    // Pattern: ...Reveal.initialize... followed by presentation.js at end
    const jsOrderRegex = /(<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/reveal\.js@[^"]+\/dist\/reveal\.js"><\/script>)\s*\n\s*<script>\s*\n([\s\S]*?Reveal\.initialize)/;
    const match = content.match(jsOrderRegex);

    if (match && !content.includes('<script src="../../assets/js/presentation.js"></script>\n    <script>')) {
        // Check if presentation.js is after the main script block
        const presentationJsAfter = /<\/script>\s*\n\s*<script src="\.\.\/\.\.\/assets\/js\/presentation\.js"><\/script>/;
        if (presentationJsAfter.test(content)) {
            // Move presentation.js to before the inline script
            content = content.replace(presentationJsAfter, '</script>');
            content = content.replace(
                /(<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/reveal\.js@[^"]+\/dist\/reveal\.js"><\/script>)\s*\n/,
                '$1\n    <script src="../../assets/js/presentation.js"></script>\n'
            );
            modified = true;
            console.log(`  - Reordered presentation.js to load before inline script`);
        }
    }

    // Clean up extra whitespace
    content = content.replace(/\n{3,}/g, '\n\n');

    if (modified) {
        fs.writeFileSync(filePath, content, 'utf8');
        return true;
    }
    return false;
}

function processDirectory(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    let fixedCount = 0;

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            fixedCount += processDirectory(fullPath);
        } else if (entry.name.endsWith('.html') && !entry.name.includes('_original')) {
            console.log(`Processing: ${path.relative(presentationsDir, fullPath)}`);
            if (fixPresentation(fullPath)) {
                fixedCount++;
            }
        }
    }

    return fixedCount;
}

console.log('Fixing V2 Presentations...\n');
const fixedCount = processDirectory(presentationsDir);
console.log(`\nDone! Fixed ${fixedCount} presentations.`);
