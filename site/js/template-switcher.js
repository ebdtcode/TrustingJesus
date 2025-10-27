/**
 * Template Switcher Module
 * Allows users to switch between different presentation templates on the fly
 * Works with Netlify static hosting - no server required
 */

const TemplateSwitcher = {
  // Available templates
  templates: {
    'blue-modern': {
      name: 'Blue Modern',
      description: 'Modern blue chevron design with professional layout'
    },
    'torn-paper': {
      name: 'Torn Paper',
      description: 'Elegant torn paper design with warm tones'
    },
    'classic': {
      name: 'Classic Dark',
      description: 'Classic presentation style with dark theme'
    }
  },

  // Current template
  currentTemplate: null,

  // Initialize the template switcher
  init() {
    this.loadSavedTemplate();
    this.createSwitcherUI();
    this.attachEventListeners();
  },

  // Load saved template preference from localStorage
  loadSavedTemplate() {
    const saved = localStorage.getItem('preferredTemplate');
    if (saved && this.templates[saved]) {
      this.currentTemplate = saved;
      this.applyTemplate(saved);
    } else {
      // Default to blue-modern if no preference saved
      this.currentTemplate = 'blue-modern';
      this.applyTemplate('blue-modern');
    }
  },

  // Create the template switcher UI
  createSwitcherUI() {
    const switcher = document.createElement('div');
    switcher.id = 'template-switcher';
    switcher.innerHTML = `
      <style>
        #template-switcher {
          position: fixed;
          top: 80px;
          right: 30px;
          z-index: 2000;
          background: rgba(20, 33, 61, 0.98);
          border-radius: 12px;
          padding: 1rem;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
          backdrop-filter: blur(10px);
          min-width: 200px;
        }

        #template-switcher.collapsed {
          padding: 0.5rem;
          min-width: auto;
        }

        #template-switcher.collapsed .switcher-content {
          display: none;
        }

        .switcher-header {
          display: flex;
          align-items: center;
          justify-content: between;
          margin-bottom: 0.5rem;
          color: #ffffff;
          font-weight: 600;
          font-size: 0.9rem;
        }

        #template-switcher.collapsed .switcher-header {
          margin-bottom: 0;
        }

        .toggle-btn {
          background: none;
          border: none;
          cursor: pointer;
          font-size: 1.2rem;
          padding: 0.25rem;
          color: #ffffff;
          transition: transform 0.3s ease;
        }

        .toggle-btn:hover {
          transform: scale(1.1);
        }

        .template-option {
          display: flex;
          align-items: center;
          padding: 0.75rem;
          margin: 0.5rem 0;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s ease;
          background: rgba(255, 255, 255, 0.1);
          border: 2px solid transparent;
        }

        .template-option:hover {
          background: rgba(255, 255, 255, 0.15);
          transform: translateX(3px);
        }

        .template-option.active {
          background: rgba(59, 130, 246, 0.3);
          border-color: #3b82f6;
        }

        .template-radio {
          width: 18px;
          height: 18px;
          margin-right: 0.75rem;
          accent-color: #2563a8;
        }

        .template-info {
          flex: 1;
        }

        .template-name {
          font-weight: 600;
          color: #ffffff;
          font-size: 0.95rem;
        }

        .template-desc {
          font-size: 0.75rem;
          color: #e6eef7;
          margin-top: 0.25rem;
        }

        @media (max-width: 768px) {
          #template-switcher {
            top: 70px;
            right: 10px;
            min-width: 180px;
          }
        }

        @media print {
          #template-switcher {
            display: none;
          }
        }
      </style>

      <div class="switcher-header">
        <span>🎨 Template</span>
        <button class="toggle-btn" id="toggle-switcher" title="Toggle template switcher">
          ▼
        </button>
      </div>

      <div class="switcher-content">
        ${Object.entries(this.templates).map(([key, template]) => `
          <div class="template-option ${key === this.currentTemplate ? 'active' : ''}" data-template="${key}">
            <input type="radio" name="template" value="${key}" class="template-radio"
                   ${key === this.currentTemplate ? 'checked' : ''}>
            <div class="template-info">
              <div class="template-name">${template.name}</div>
              <div class="template-desc">${template.description}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    document.body.appendChild(switcher);
  },

  // Attach event listeners
  attachEventListeners() {
    // Toggle collapse/expand
    const toggleBtn = document.getElementById('toggle-switcher');
    const switcher = document.getElementById('template-switcher');

    toggleBtn.addEventListener('click', () => {
      switcher.classList.toggle('collapsed');
      toggleBtn.textContent = switcher.classList.contains('collapsed') ? '▶' : '▼';
    });

    // Template selection
    document.querySelectorAll('.template-option').forEach(option => {
      option.addEventListener('click', () => {
        const template = option.dataset.template;
        this.switchTemplate(template);
      });
    });
  },

  // Switch to a different template
  switchTemplate(templateKey) {
    if (!this.templates[templateKey]) {
      console.error('Unknown template:', templateKey);
      return;
    }

    // Update UI
    document.querySelectorAll('.template-option').forEach(opt => {
      opt.classList.remove('active');
      opt.querySelector('input').checked = false;
    });

    const selectedOption = document.querySelector(`[data-template="${templateKey}"]`);
    if (selectedOption) {
      selectedOption.classList.add('active');
      selectedOption.querySelector('input').checked = true;
    }

    // Apply template
    this.applyTemplate(templateKey);

    // Save preference
    localStorage.setItem('preferredTemplate', templateKey);
    this.currentTemplate = templateKey;
  },

  // Apply template styles and structure
  applyTemplate(templateKey) {
    const root = document.documentElement;
    const body = document.body;

    // Remove existing template classes
    body.className = body.className.replace(/template-\w+/g, '').trim();

    // Add new template class
    body.classList.add(`template-${templateKey}`);

    // Apply template-specific CSS variables and styles
    switch (templateKey) {
      case 'blue-modern':
        this.applyBlueModernTheme();
        break;
      case 'torn-paper':
        this.applyTornPaperTheme();
        break;
      case 'classic':
        this.applyClassicTheme();
        break;
    }

    // Trigger custom event for other scripts to respond
    window.dispatchEvent(new CustomEvent('templateChanged', {
      detail: { template: templateKey }
    }));
  },

  // Apply Blue Modern theme
  applyBlueModernTheme() {
    const root = document.documentElement;

    // Primary colors
    root.style.setProperty('--primary-blue', '#2563a8');
    root.style.setProperty('--dark-blue', '#1e4a7c');
    root.style.setProperty('--accent-blue', '#3b82f6');
    root.style.setProperty('--accent-color', '#3b82f6');
    root.style.setProperty('--white', '#ffffff');
    root.style.setProperty('--light-gray', '#f5f5f5');
    root.style.setProperty('--dark-gray', '#333333');

    // Update body background
    document.body.style.background = 'linear-gradient(135deg, #2563a8 0%, #1e4a7c 100%)';

    // Inject template styles
    this.injectTemplateStyles('blue-modern');
  },

  // Apply Torn Paper theme
  applyTornPaperTheme() {
    const root = document.documentElement;

    // Warm tones theme
    root.style.setProperty('--primary-blue', '#8b4513');
    root.style.setProperty('--dark-blue', '#654321');
    root.style.setProperty('--accent-blue', '#cd853f');
    root.style.setProperty('--accent-color', '#cd853f');
    root.style.setProperty('--white', '#fffef7');
    root.style.setProperty('--light-gray', '#f5f0e8');
    root.style.setProperty('--dark-gray', '#3e2723');

    // Warm background
    document.body.style.background = 'linear-gradient(135deg, #8b4513 0%, #654321 100%)';

    // Inject template styles
    this.injectTemplateStyles('torn-paper');
  },

  // Apply Classic theme
  applyClassicTheme() {
    const root = document.documentElement;

    // Classic dark theme
    root.style.setProperty('--primary-blue', '#14213d');
    root.style.setProperty('--dark-blue', '#0a1128');
    root.style.setProperty('--accent-blue', '#ffd166');
    root.style.setProperty('--accent-color', '#ffd166');
    root.style.setProperty('--white', '#ffffff');
    root.style.setProperty('--light-gray', '#f5f5f5');
    root.style.setProperty('--dark-gray', '#333333');

    // Classic background
    document.body.style.background = 'linear-gradient(135deg, #14213d 0%, #1f4068 100%)';

    // Inject template styles
    this.injectTemplateStyles('classic');
  },

  // Inject template-specific CSS
  injectTemplateStyles(templateKey) {
    // Remove existing dynamic styles
    const existingStyle = document.getElementById('template-dynamic-styles');
    if (existingStyle) {
      existingStyle.remove();
    }

    // Create new style element
    const styleEl = document.createElement('style');
    styleEl.id = 'template-dynamic-styles';

    let css = '';

    if (templateKey === 'blue-modern') {
      css = `
        /* Blue Modern Template Enhancements */
        .slide.active {
          animation: slideInBlueModern 0.6s ease;
        }

        @keyframes slideInBlueModern {
          from {
            opacity: 0;
            transform: translateX(30px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .scripture, .prayer-points {
          border-left-color: var(--accent-blue) !important;
        }

        .slide h2, .presentation h2 {
          color: var(--accent-blue) !important;
        }

        .emphasis {
          color: var(--accent-blue) !important;
        }

        .sidebar {
          background: rgba(30, 74, 124, 0.95) !important;
        }

        /* Fix contrast: Dark text on white backgrounds, white text on dark backgrounds */

        /* White background sections need dark text */
        .content-right,
        .content-right *,
        .title-content,
        .title-content *,
        .slide[style*="background: white"],
        .slide[style*="background: #fff"] {
          color: #333 !important;
        }

        .content-right h1,
        .content-right h2,
        .content-right h3,
        .title-content h1,
        .title-content h2,
        .title-content h3 {
          color: #333 !important;
        }

        /* Default slide text - white on dark */
        .slide {
          color: var(--white) !important;
        }

        .slide h1, .slide h3 {
          color: var(--white) !important;
        }

        .slide h2 {
          color: var(--accent-blue) !important;
        }

        /* List items */
        .content-list li, ul li, ol li {
          background: transparent !important;
        }

        mark {
          background: transparent !important;
        }
      `;
    } else if (templateKey === 'torn-paper') {
      css = `
        /* Torn Paper Template Enhancements */
        .slide.active {
          animation: fadeInTornPaper 0.8s ease;
        }

        @keyframes fadeInTornPaper {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .scripture, .prayer-points {
          background: var(--white) !important;
          color: var(--dark-gray) !important;
          border-left-color: var(--accent-color) !important;
        }

        .scripture-ref {
          color: #1f4068 !important;
        }

        .scripture-text {
          color: var(--dark-gray) !important;
        }

        .slide h2, .presentation h2 {
          color: #1f4068 !important;
          font-family: Georgia, serif !important;
        }

        .emphasis {
          color: #1f4068 !important;
        }

        .sidebar {
          background: rgba(139, 69, 19, 0.95) !important;
        }

        .content-right {
          background: var(--white) !important;
          color: var(--dark-gray) !important;
        }

        .title-content {
          background: var(--white) !important;
          color: var(--dark-gray) !important;
        }

        .scripture-slide {
          background: var(--white) !important;
          color: var(--dark-gray) !important;
        }

        /* Fix contrast for torn-paper theme */

        /* Default slide text - dark on warm background */
        .slide {
          color: var(--dark-gray) !important;
        }

        .slide h1, .slide h3, .slide h4 {
          color: var(--dark-gray) !important;
        }

        /* White/light background sections */
        .content-right,
        .content-right *,
        .title-content,
        .title-content * {
          color: var(--dark-gray) !important;
        }

        /* List items */
        .content-list li, ul li, ol li {
          background: transparent !important;
          color: var(--dark-gray) !important;
        }

        mark {
          background: transparent !important;
          color: var(--dark-gray) !important;
        }

        /* Keep accent color for emphasis */
        .emphasis {
          color: #1f4068 !important;
        }
      `;
    } else if (templateKey === 'classic') {
      css = `
        /* Classic Template Enhancements */
        .slide.active {
          animation: fadeInClassic 0.5s ease;
        }

        @keyframes fadeInClassic {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .scripture, .prayer-points {
          background: rgba(255, 255, 255, 0.14) !important;
          border-left-color: var(--accent-color) !important;
        }

        .slide h2, .presentation h2 {
          color: #1f4068 !important;
        }

        .emphasis {
          color: #1f4068 !important;
        }

        .sidebar {
          background: rgba(20, 33, 61, 0.95) !important;
        }

        /* Fix contrast for classic theme */

        /* White background sections need dark text */
        .content-right,
        .content-right *,
        .title-content,
        .title-content *,
        .slide[style*="background: white"],
        .slide[style*="background: #fff"] {
          color: #333 !important;
        }

        .content-right h1,
        .content-right h2,
        .content-right h3,
        .title-content h1,
        .title-content h2,
        .title-content h3 {
          color: #333 !important;
        }

        /* Default slide text - white on dark */
        .slide {
          color: var(--white) !important;
        }

        .slide h1, .slide h3 {
          color: var(--white) !important;
        }

        .slide h2 {
          color: #1f4068 !important;
        }

        /* List items */
        .content-list li, ul li, ol li {
          background: transparent !important;
        }

        mark {
          background: transparent !important;
        }

        .emphasis {
          color: #1f4068 !important;
        }
      `;
    }

    styleEl.textContent = css;
    document.head.appendChild(styleEl);
  }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => TemplateSwitcher.init());
} else {
  TemplateSwitcher.init();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TemplateSwitcher;
}
