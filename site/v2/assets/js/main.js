/**
 * Prayer Trusting Jesus - Main JavaScript v2
 * Shared functionality across all pages
 */

(function() {
  'use strict';

  // ============================================
  // Navigation
  // ============================================

  const nav = {
    init() {
      this.toggle = document.querySelector('.nav-toggle');
      this.mobileMenu = document.querySelector('.nav-mobile');
      this.links = document.querySelectorAll('.nav-link');

      if (this.toggle && this.mobileMenu) {
        this.toggle.addEventListener('click', () => this.toggleMenu());

        // Close menu on link click
        this.mobileMenu.querySelectorAll('a').forEach(link => {
          link.addEventListener('click', () => this.closeMenu());
        });

        // Close menu on escape key
        document.addEventListener('keydown', (e) => {
          if (e.key === 'Escape') this.closeMenu();
        });
      }

      // Highlight current page
      this.highlightCurrentPage();

      // Shrink nav on scroll
      this.handleScroll();
    },

    toggleMenu() {
      const isOpen = this.mobileMenu.classList.toggle('open');
      this.toggle.setAttribute('aria-expanded', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    },

    closeMenu() {
      this.mobileMenu.classList.remove('open');
      this.toggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    },

    highlightCurrentPage() {
      const currentPath = window.location.pathname;
      this.links.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href.replace('.html', ''))) {
          link.classList.add('active');
        }
      });
    },

    handleScroll() {
      const navEl = document.querySelector('.nav');
      if (!navEl) return;

      let lastScroll = 0;
      window.addEventListener('scroll', () => {
        const currentScroll = window.scrollY;

        if (currentScroll > 100) {
          navEl.classList.add('scrolled');
        } else {
          navEl.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
      }, { passive: true });
    }
  };

  // ============================================
  // Scroll Reveal Animation
  // ============================================

  const scrollReveal = {
    init() {
      this.elements = document.querySelectorAll('.reveal');
      if (this.elements.length === 0) return;

      // Use Intersection Observer for performance
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach(entry => {
              if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
              }
            });
          },
          {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
          }
        );

        this.elements.forEach(el => observer.observe(el));
      } else {
        // Fallback for older browsers
        this.elements.forEach(el => el.classList.add('visible'));
      }
    }
  };

  // ============================================
  // Smooth Scroll for Anchor Links
  // ============================================

  const smoothScroll = {
    init() {
      document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
          const href = anchor.getAttribute('href');
          if (href === '#') return;

          const target = document.querySelector(href);
          if (target) {
            e.preventDefault();
            const navHeight = document.querySelector('.nav')?.offsetHeight || 0;
            const targetPosition = target.getBoundingClientRect().top + window.scrollY - navHeight - 20;

            window.scrollTo({
              top: targetPosition,
              behavior: 'smooth'
            });

            // Update URL without jumping
            history.pushState(null, '', href);
          }
        });
      });
    }
  };

  // ============================================
  // Theme Toggle (Light/Dark)
  // ============================================

  const theme = {
    init() {
      this.toggle = document.querySelector('[data-theme-toggle]');
      if (!this.toggle) return;

      // Check for saved preference or system preference
      const savedTheme = localStorage.getItem('theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

      if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.classList.add('dark');
      }

      this.toggle.addEventListener('click', () => this.toggleTheme());
    },

    toggleTheme() {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }
  };

  // ============================================
  // Lazy Loading Images
  // ============================================

  const lazyLoad = {
    init() {
      if ('loading' in HTMLImageElement.prototype) {
        // Native lazy loading supported
        document.querySelectorAll('img[data-src]').forEach(img => {
          img.src = img.dataset.src;
          img.loading = 'lazy';
        });
      } else if ('IntersectionObserver' in window) {
        // Fallback to Intersection Observer
        const observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const img = entry.target;
              img.src = img.dataset.src;
              img.classList.add('loaded');
              observer.unobserve(img);
            }
          });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
          observer.observe(img);
        });
      }
    }
  };

  // ============================================
  // Accordion Component
  // ============================================

  const accordion = {
    init() {
      document.querySelectorAll('[data-accordion]').forEach(container => {
        const triggers = container.querySelectorAll('[data-accordion-trigger]');

        triggers.forEach(trigger => {
          trigger.addEventListener('click', () => {
            const content = trigger.nextElementSibling;
            const isOpen = trigger.getAttribute('aria-expanded') === 'true';

            // Close all others if single mode
            if (container.dataset.accordion === 'single') {
              triggers.forEach(t => {
                t.setAttribute('aria-expanded', 'false');
                t.nextElementSibling.hidden = true;
              });
            }

            trigger.setAttribute('aria-expanded', !isOpen);
            content.hidden = isOpen;
          });
        });
      });
    }
  };

  // ============================================
  // Tab Component
  // ============================================

  const tabs = {
    init() {
      document.querySelectorAll('[data-tabs]').forEach(container => {
        const tabButtons = container.querySelectorAll('[role="tab"]');
        const tabPanels = container.querySelectorAll('[role="tabpanel"]');

        tabButtons.forEach((button, index) => {
          button.addEventListener('click', () => {
            this.activateTab(tabButtons, tabPanels, index);
          });

          button.addEventListener('keydown', (e) => {
            let newIndex;
            if (e.key === 'ArrowRight') {
              newIndex = (index + 1) % tabButtons.length;
            } else if (e.key === 'ArrowLeft') {
              newIndex = (index - 1 + tabButtons.length) % tabButtons.length;
            } else if (e.key === 'Home') {
              newIndex = 0;
            } else if (e.key === 'End') {
              newIndex = tabButtons.length - 1;
            }

            if (newIndex !== undefined) {
              e.preventDefault();
              tabButtons[newIndex].focus();
              this.activateTab(tabButtons, tabPanels, newIndex);
            }
          });
        });
      });
    },

    activateTab(buttons, panels, activeIndex) {
      buttons.forEach((button, index) => {
        const isActive = index === activeIndex;
        button.setAttribute('aria-selected', isActive);
        button.tabIndex = isActive ? 0 : -1;
        panels[index].hidden = !isActive;
      });
    }
  };

  // ============================================
  // Modal Component
  // ============================================

  const modal = {
    init() {
      // Open triggers
      document.querySelectorAll('[data-modal-open]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
          e.preventDefault();
          const modalId = trigger.dataset.modalOpen;
          this.open(modalId);
        });
      });

      // Close triggers
      document.querySelectorAll('[data-modal-close]').forEach(trigger => {
        trigger.addEventListener('click', () => this.closeActive());
      });

      // Close on backdrop click
      document.querySelectorAll('.modal').forEach(modalEl => {
        modalEl.addEventListener('click', (e) => {
          if (e.target === modalEl) this.closeActive();
        });
      });

      // Close on escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.closeActive();
      });
    },

    open(id) {
      const modalEl = document.getElementById(id);
      if (!modalEl) return;

      modalEl.classList.add('open');
      modalEl.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';

      // Focus first focusable element
      const focusable = modalEl.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusable) focusable.focus();
    },

    closeActive() {
      const activeModal = document.querySelector('.modal.open');
      if (!activeModal) return;

      activeModal.classList.remove('open');
      activeModal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }
  };

  // ============================================
  // Form Validation
  // ============================================

  const forms = {
    init() {
      document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', (e) => {
          if (!this.validate(form)) {
            e.preventDefault();
          }
        });

        // Real-time validation
        form.querySelectorAll('input, textarea, select').forEach(field => {
          field.addEventListener('blur', () => this.validateField(field));
          field.addEventListener('input', () => {
            if (field.classList.contains('invalid')) {
              this.validateField(field);
            }
          });
        });
      });
    },

    validate(form) {
      let isValid = true;
      form.querySelectorAll('[required]').forEach(field => {
        if (!this.validateField(field)) {
          isValid = false;
        }
      });
      return isValid;
    },

    validateField(field) {
      const value = field.value.trim();
      const type = field.type;
      let isValid = true;

      // Required check
      if (field.required && !value) {
        isValid = false;
      }

      // Email check
      if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        isValid = emailRegex.test(value);
      }

      // Update UI
      field.classList.toggle('invalid', !isValid);
      field.classList.toggle('valid', isValid && value);

      // Update error message
      const errorEl = field.parentElement.querySelector('.error-message');
      if (errorEl) {
        errorEl.hidden = isValid;
      }

      return isValid;
    }
  };

  // ============================================
  // Toast Notifications
  // ============================================

  const toast = {
    container: null,

    init() {
      // Create toast container if it doesn't exist
      if (!document.querySelector('.toast-container')) {
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        this.container.setAttribute('aria-live', 'polite');
        document.body.appendChild(this.container);
      } else {
        this.container = document.querySelector('.toast-container');
      }
    },

    show(message, type = 'info', duration = 5000) {
      const toastEl = document.createElement('div');
      toastEl.className = 'toast toast-' + type;

      const messageSpan = document.createElement('span');
      messageSpan.className = 'toast-message';
      messageSpan.textContent = message;

      const closeBtn = document.createElement('button');
      closeBtn.className = 'toast-close';
      closeBtn.setAttribute('aria-label', 'Close notification');
      closeBtn.textContent = '\u00D7';

      toastEl.appendChild(messageSpan);
      toastEl.appendChild(closeBtn);

      this.container.appendChild(toastEl);

      // Animate in
      requestAnimationFrame(() => {
        toastEl.classList.add('visible');
      });

      // Close button
      closeBtn.addEventListener('click', () => {
        this.dismiss(toastEl);
      });

      // Auto dismiss
      if (duration > 0) {
        setTimeout(() => this.dismiss(toastEl), duration);
      }
    },

    dismiss(toastEl) {
      toastEl.classList.remove('visible');
      toastEl.addEventListener('transitionend', () => toastEl.remove());
    }
  };

  // ============================================
  // Utility Functions
  // ============================================

  const utils = {
    // Debounce function
    debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },

    // Throttle function
    throttle(func, limit) {
      let inThrottle;
      return function(...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    },

    // Format date
    formatDate(date, options = {}) {
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        ...options
      }).format(new Date(date));
    },

    // Copy to clipboard
    async copyToClipboard(text) {
      try {
        await navigator.clipboard.writeText(text);
        toast.show('Copied to clipboard', 'success', 2000);
        return true;
      } catch (err) {
        console.error('Failed to copy:', err);
        return false;
      }
    }
  };

  // ============================================
  // Initialize on DOM Ready
  // ============================================

  function init() {
    nav.init();
    scrollReveal.init();
    smoothScroll.init();
    theme.init();
    lazyLoad.init();
    accordion.init();
    tabs.init();
    modal.init();
    forms.init();
    toast.init();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose utilities globally
  window.PTJ = {
    toast,
    utils,
    modal
  };

})();
