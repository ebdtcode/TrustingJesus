# Prayer Trusting Jesus - Project Rules

## Mobile-First Design (MANDATORY)

All web development in this project MUST follow mobile-first design principles:

### Requirements

1. **Start with mobile viewport** - Design and implement for 320px-480px screens first
2. **Progressive enhancement** - Add complexity for larger screens using `min-width` media queries
3. **Test on mobile before desktop** - Use Playwright or browser dev tools to verify mobile rendering
4. **Reveal.js presentations** - Use base dimensions of 960x700 or smaller (NOT 1920x1080)

### CSS Media Query Order

```css
/* Mobile styles first (default) */
.element {
    font-size: 14px;
    padding: 0.5rem;
}

/* Tablet and up */
@media screen and (min-width: 768px) {
    .element {
        font-size: 16px;
        padding: 1rem;
    }
}

/* Desktop and up */
@media screen and (min-width: 1024px) {
    .element {
        font-size: 18px;
        padding: 1.5rem;
    }
}
```

### Reveal.js Configuration

For presentations, always use mobile-friendly settings:

```javascript
Reveal.initialize({
    width: 960,
    height: 700,
    margin: 0.1,
    minScale: 0.2,
    maxScale: 2.0,
    // ...
});
```

### Testing Checklist

Before deploying any UI changes:
- [ ] Test on iPhone SE (375x667)
- [ ] Test on iPhone 12/13 (390x844)
- [ ] Test on iPad (768x1024)
- [ ] Test on Desktop (1920x1080)
- [ ] Verify touch targets are at least 44x44px
- [ ] Ensure text is readable without zooming
