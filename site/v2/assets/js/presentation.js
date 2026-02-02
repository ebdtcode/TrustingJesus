/**
 * V2 Presentation JavaScript Module
 *
 * Provides standardized Reveal.js initialization and navigation features
 * for all v2 presentations.
 *
 * Features:
 * - Mobile-friendly Reveal.js configuration (960x700)
 * - Home button keyboard shortcut (H key)
 * - Slide navigator modal
 * - Accessibility enhancements
 *
 * Note: innerHTML usage in this file is safe as all content is static
 * string literals defined in code, not user input.
 */

(function() {
    'use strict';

    // Configuration defaults
    const CONFIG = {
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
        help: true
    };

    // Home URL - relative path to v2 presentations page
    let homeUrl = '../../presentations.html';

    /**
     * Initialize Reveal.js with v2 settings
     * @param {Object} options - Optional configuration overrides
     * @returns {Object} Reveal instance
     */
    function initReveal(options = {}) {
        const config = { ...CONFIG, ...options };

        Reveal.initialize(config);

        // Add home button keyboard shortcut
        Reveal.addKeyBinding({ keyCode: 72, key: 'H', description: 'Go home' }, () => {
            window.location.href = homeUrl;
        });

        // Initialize slide navigator if elements exist
        initSlideNavigator();

        return Reveal;
    }

    /**
     * Set the home URL for the home button and H key
     * @param {string} url - The URL to navigate to
     */
    function setHomeUrl(url) {
        homeUrl = url;

        // Update home button href if it exists
        const homeBtn = document.querySelector('.home-btn');
        if (homeBtn) {
            homeBtn.setAttribute('href', url);
        }
    }

    /**
     * Initialize the slide navigator modal
     */
    function initSlideNavigator() {
        const trigger = document.querySelector('.slide-nav-trigger');
        const modal = document.getElementById('slideNavModal');
        const closeBtn = document.querySelector('.slide-nav-close');
        const grid = document.getElementById('slideNavGrid');
        const countEl = document.getElementById('slideNavCount');

        if (!trigger || !modal || !grid) {
            return;
        }

        // Build slide list
        function buildSlideList() {
            const slides = Reveal.getSlides();
            const currentSlide = Reveal.getCurrentSlide();

            // Clear existing items
            while (grid.firstChild) {
                grid.removeChild(grid.firstChild);
            }

            if (countEl) {
                countEl.textContent = slides.length + ' slides';
            }

            slides.forEach((slide, index) => {
                const item = document.createElement('button');
                item.className = 'slide-nav-item';
                if (slide === currentSlide) {
                    item.classList.add('current');
                }

                // Get slide title from h1, h2, or h3
                const title = slide.querySelector('h1, h2, h3');
                const titleText = title ? title.textContent.trim() : 'Slide ' + (index + 1);

                // Get room badge if present
                const badge = slide.querySelector('.room-badge, .section-badge');
                const badgeText = badge ? badge.textContent.trim() : '';

                // Create number element
                const numberDiv = document.createElement('div');
                numberDiv.className = 'slide-number';
                numberDiv.textContent = 'Slide ' + (index + 1);

                // Create title element
                const titleDiv = document.createElement('div');
                titleDiv.className = 'slide-title';
                titleDiv.textContent = badgeText ? badgeText + ': ' + titleText : titleText;

                item.appendChild(numberDiv);
                item.appendChild(titleDiv);

                item.addEventListener('click', () => {
                    Reveal.slide(index);
                    closeModal();
                });

                grid.appendChild(item);
            });
        }

        // Open modal
        function openModal() {
            buildSlideList();
            modal.classList.add('active');
            modal.setAttribute('aria-hidden', 'false');

            // Focus first item
            const firstItem = grid.querySelector('.slide-nav-item');
            if (firstItem) {
                firstItem.focus();
            }

            // Trap focus in modal
            document.addEventListener('keydown', handleModalKeydown);
        }

        // Close modal
        function closeModal() {
            modal.classList.remove('active');
            modal.setAttribute('aria-hidden', 'true');
            document.removeEventListener('keydown', handleModalKeydown);
            trigger.focus();
        }

        // Handle keyboard navigation in modal
        function handleModalKeydown(e) {
            if (e.key === 'Escape') {
                closeModal();
                return;
            }

            // Tab trapping
            if (e.key === 'Tab') {
                const focusableElements = modal.querySelectorAll('button, [tabindex]:not([tabindex="-1"])');
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];

                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        }

        // Event listeners
        trigger.addEventListener('click', openModal);

        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Add keyboard shortcut for navigator (G key)
        Reveal.addKeyBinding({ keyCode: 71, key: 'G', description: 'Slide navigator' }, openModal);
    }

    /**
     * Create and inject slide navigator HTML if not present
     */
    function injectSlideNavigator() {
        // Check if navigator already exists
        if (document.querySelector('.slide-nav-trigger')) {
            return;
        }

        // Create trigger button
        const trigger = document.createElement('button');
        trigger.className = 'slide-nav-trigger';
        trigger.setAttribute('aria-label', 'Open slide navigator');
        trigger.setAttribute('title', 'View all slides (G)');

        const triggerSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        triggerSvg.setAttribute('viewBox', '0 0 24 24');
        triggerSvg.setAttribute('fill', 'currentColor');
        triggerSvg.setAttribute('aria-hidden', 'true');

        const rects = [
            { x: '3', y: '3', width: '7', height: '7', rx: '1' },
            { x: '14', y: '3', width: '7', height: '7', rx: '1' },
            { x: '3', y: '14', width: '7', height: '7', rx: '1' },
            { x: '14', y: '14', width: '7', height: '7', rx: '1' }
        ];

        rects.forEach(attrs => {
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            Object.entries(attrs).forEach(([key, value]) => rect.setAttribute(key, value));
            triggerSvg.appendChild(rect);
        });

        trigger.appendChild(triggerSvg);

        // Create modal structure
        const modal = document.createElement('div');
        modal.className = 'slide-nav-modal';
        modal.id = 'slideNavModal';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-label', 'Slide navigator');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-hidden', 'true');

        // Create header
        const header = document.createElement('div');
        header.className = 'slide-nav-header';

        const headerLeft = document.createElement('div');
        const h2 = document.createElement('h2');
        h2.textContent = 'Slide Navigator';
        headerLeft.appendChild(h2);

        const countSpan = document.createElement('span');
        countSpan.className = 'slide-count';
        countSpan.id = 'slideNavCount';
        headerLeft.appendChild(countSpan);

        // Create close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'slide-nav-close';
        closeBtn.setAttribute('aria-label', 'Close navigator');

        const closeSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        closeSvg.setAttribute('viewBox', '0 0 24 24');
        closeSvg.setAttribute('fill', 'none');
        closeSvg.setAttribute('stroke', 'currentColor');
        closeSvg.setAttribute('stroke-width', '2');
        closeSvg.setAttribute('aria-hidden', 'true');

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M18 6L6 18M6 6l12 12');
        closeSvg.appendChild(path);
        closeBtn.appendChild(closeSvg);

        header.appendChild(headerLeft);
        header.appendChild(closeBtn);

        // Create content area
        const content = document.createElement('div');
        content.className = 'slide-nav-content';

        const grid = document.createElement('div');
        grid.className = 'slide-nav-grid';
        grid.id = 'slideNavGrid';
        content.appendChild(grid);

        modal.appendChild(header);
        modal.appendChild(content);

        document.body.appendChild(trigger);
        document.body.appendChild(modal);
    }

    /**
     * Create and inject home button HTML if not present
     * @param {string} url - The home URL
     */
    function injectHomeButton(url) {
        url = url || '../../presentations.html';

        // Check if home button already exists
        if (document.querySelector('.home-btn')) {
            return;
        }

        const btn = document.createElement('a');
        btn.className = 'home-btn';
        btn.href = url;
        btn.setAttribute('aria-label', 'Return to presentations list');

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('aria-hidden', 'true');

        const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        pathEl.setAttribute('d', 'M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z');
        svg.appendChild(pathEl);

        const span = document.createElement('span');
        span.textContent = 'Home';

        btn.appendChild(svg);
        btn.appendChild(span);

        document.body.appendChild(btn);
        homeUrl = url;
    }

    /**
     * Create and inject skip link for accessibility
     */
    function injectSkipLink() {
        // Check if skip link already exists
        if (document.querySelector('.skip-link')) {
            return;
        }

        const link = document.createElement('a');
        link.className = 'skip-link';
        link.href = '#main-content';
        link.textContent = 'Skip to content';

        document.body.insertBefore(link, document.body.firstChild);
    }

    /**
     * Calculate relative path to v2 presentations based on current location
     * @returns {string} Relative path to presentations.html
     */
    function calculateHomeUrl() {
        const path = window.location.pathname;

        // Count directory depth from /presentations/
        const presentationsIndex = path.indexOf('/presentations/');
        if (presentationsIndex === -1) {
            return 'presentations.html';
        }

        const afterPresentations = path.substring(presentationsIndex + '/presentations/'.length);
        const depth = (afterPresentations.match(/\//g) || []).length;

        // Build relative path
        return '../'.repeat(depth + 1) + 'presentations.html';
    }

    // Export functions to global scope
    window.V2Presentation = {
        init: initReveal,
        setHomeUrl: setHomeUrl,
        injectSlideNavigator: injectSlideNavigator,
        injectHomeButton: injectHomeButton,
        injectSkipLink: injectSkipLink,
        calculateHomeUrl: calculateHomeUrl,
        CONFIG: CONFIG
    };

    // Auto-initialize if Reveal is available and auto-init attribute is set
    document.addEventListener('DOMContentLoaded', () => {
        const autoInit = document.querySelector('[data-v2-auto-init]');
        if (autoInit && typeof Reveal !== 'undefined') {
            // Calculate home URL based on file location
            const calculatedHomeUrl = calculateHomeUrl();

            injectSkipLink();
            injectHomeButton(calculatedHomeUrl);
            injectSlideNavigator();
            initReveal();
        }
    });

    // Also listen for Reveal.js 'ready' event to initialize navigator
    // This handles cases where Reveal.initialize() is called directly
    if (typeof Reveal !== 'undefined') {
        // Wait a tick to ensure Reveal is set up
        setTimeout(() => {
            if (Reveal.isReady && Reveal.isReady()) {
                initSlideNavigator();
            } else {
                Reveal.on('ready', () => {
                    initSlideNavigator();
                });
            }
        }, 0);
    }
})();
