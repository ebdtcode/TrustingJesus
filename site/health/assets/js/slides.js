/* Health Presentation Slides Navigation JavaScript */

// Slide navigation state
let currentSlide = 1;
let totalSlides = 0;
let slideTitles = [];

/**
 * Initialize the presentation
 * @param {Array} titles - Array of slide titles for sidebar navigation
 * @param {Array} sectionBreaks - Array of slide indices that should be marked as section breaks
 */
function initPresentation(titles, sectionBreaks = []) {
  slideTitles = titles;
  totalSlides = document.querySelectorAll('.slide').length;
  document.getElementById('total-slides').textContent = totalSlides;

  generateSidebar(sectionBreaks);
  showSlide(currentSlide);
}

/**
 * Generate sidebar navigation
 * @param {Array} sectionBreaks - Array of slide indices for section breaks
 */
function generateSidebar(sectionBreaks = []) {
  const sidebarNav = document.getElementById('sidebarNav');
  if (!sidebarNav) return;

  sidebarNav.innerHTML = '';

  slideTitles.forEach((title, index) => {
    const item = document.createElement('div');
    item.className = 'sidebar-item';

    // Mark section breaks
    if (sectionBreaks.includes(index)) {
      item.classList.add('section');
    }

    if (index === currentSlide - 1) {
      item.classList.add('active');
    }

    item.innerHTML = `
      <span class="slide-num">${index + 1}</span>
      <span>${title}</span>
    `;

    item.onclick = () => {
      showSlide(index + 1);
    };

    sidebarNav.appendChild(item);
  });
}

/**
 * Show specific slide
 * @param {number} n - Slide number to show
 */
function showSlide(n) {
  const slides = document.querySelectorAll('.slide');
  if (n > totalSlides) n = 1;
  if (n < 1) n = totalSlides;
  currentSlide = n;

  slides.forEach(s => s.classList.remove('active'));
  slides[currentSlide - 1].classList.add('active');

  const currentSlideEl = document.getElementById('current-slide');
  if (currentSlideEl) {
    currentSlideEl.textContent = currentSlide;
  }

  // Update navigation buttons
  updateNavigationButtons();

  // Update sidebar
  updateSidebarActive();
}

/**
 * Update navigation button states
 */
function updateNavigationButtons() {
  const prevBtn = document.querySelector('.nav-btn');
  const nextBtn = document.querySelectorAll('.nav-btn')[1];

  if (prevBtn) prevBtn.disabled = currentSlide === 1;
  if (nextBtn) nextBtn.disabled = currentSlide === totalSlides;
}

/**
 * Update sidebar active state
 */
function updateSidebarActive() {
  const items = document.querySelectorAll('.sidebar-item:not(.section)');
  items.forEach((item, index) => {
    if (index === currentSlide - 1) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
}

/**
 * Navigate to next slide
 */
function nextSlide() {
  if (currentSlide < totalSlides) {
    showSlide(currentSlide + 1);
  }
}

/**
 * Navigate to previous slide
 */
function previousSlide() {
  if (currentSlide > 1) {
    showSlide(currentSlide - 1);
  }
}

/**
 * Toggle sidebar visibility (mobile)
 */
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.classList.toggle('open');
  }
}

/**
 * Keyboard navigation
 */
document.addEventListener('keydown', function(event) {
  switch(event.key) {
    case 'ArrowRight':
    case 'ArrowDown':
    case ' ': // Space
    case 'Enter':
      nextSlide();
      event.preventDefault();
      break;
    case 'ArrowLeft':
    case 'ArrowUp':
      previousSlide();
      event.preventDefault();
      break;
    case 'Home':
      showSlide(1);
      event.preventDefault();
      break;
    case 'End':
      showSlide(totalSlides);
      event.preventDefault();
      break;
    case 'PageDown':
      showSlide(Math.min(currentSlide + 10, totalSlides));
      event.preventDefault();
      break;
    case 'PageUp':
      showSlide(Math.max(currentSlide - 10, 1));
      event.preventDefault();
      break;
  }
});

/**
 * Touch/swipe support for mobile
 */
let startX = 0;
let startY = 0;

document.addEventListener('touchstart', (e) => {
  startX = e.touches[0].clientX;
  startY = e.touches[0].clientY;
});

document.addEventListener('touchend', (e) => {
  const endX = e.changedTouches[0].clientX;
  const endY = e.changedTouches[0].clientY;
  const deltaX = endX - startX;
  const deltaY = endY - startY;

  // Only trigger if horizontal swipe is longer than vertical and over 50px
  if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
    if (deltaX > 0) {
      previousSlide(); // Swipe right = previous
    } else {
      nextSlide();  // Swipe left = next
    }
  }
});

// Export functions for use in presentations
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initPresentation,
    showSlide,
    nextSlide,
    previousSlide,
    toggleSidebar
  };
}
