"""Render structured slide JSON into v2 Reveal.js HTML presentations.

Produces HTML matching the stained-glass sanctuary theme used in
site/v2/presentations/sermons/*.html with:
  - Reveal.js v5.1.0 CDN
  - Cinzel + EB Garamond fonts
  - presentation-theme.css
  - Slide navigator
  - Fragment animations
  - Accessible markup
"""

from __future__ import annotations

import html
import logging
import re

logger = logging.getLogger(__name__)

CATEGORY_BADGES = {
    "sermon": ("Sermon", "linear-gradient(135deg, #1d4ed8, #3b82f6)"),
    "prayer": ("Prayer", "linear-gradient(135deg, #d97706, #f59e0b)"),
    "grace": ("Grace", "linear-gradient(135deg, #7c3aed, #a78bfa)"),
    "faith": ("Faith", "linear-gradient(135deg, #047857, #34d399)"),
    "family": ("Family", "linear-gradient(135deg, #be123c, #fb7185)"),
    "marriage": ("Marriage", "linear-gradient(135deg, #be185d, #f472b6)"),
    "names-of-god": ("Names of God", "linear-gradient(135deg, #0d9488, #5eead4)"),
    "personal-development": ("Growth", "linear-gradient(135deg, #059669, #6ee7b7)"),
}


def render_presentation(slides_data: dict) -> str:
    """Render a slides JSON dict into a complete HTML presentation."""
    title = _esc(slides_data.get("title", "Presentation"))
    speaker = _esc(slides_data.get("speaker", ""))
    date = _esc(slides_data.get("date", ""))
    category = slides_data.get("category", "sermon")
    badge_label, badge_gradient = CATEGORY_BADGES.get(
        category, CATEGORY_BADGES["sermon"]
    )

    slides_html = []
    nav_items = []

    for i, slide in enumerate(slides_data.get("slides", [])):
        slide_type = slide.get("type", "content")
        heading = _esc(slide.get("heading", ""))

        if slide_type == "title":
            slides_html.append(_render_title_slide(slide, badge_label, badge_gradient))
            nav_items.append(("title", heading or title))
        elif slide_type == "scripture":
            slides_html.append(_render_scripture_slide(slide))
            nav_items.append(("scripture", heading))
        elif slide_type == "prayer":
            slides_html.append(_render_prayer_slide(slide))
            nav_items.append(("prayer", heading))
        elif slide_type == "application":
            slides_html.append(_render_application_slide(slide))
            nav_items.append(("application", heading))
        elif slide_type == "closing":
            slides_html.append(_render_closing_slide(slide))
            nav_items.append(("closing", heading))
        else:
            slides_html.append(_render_content_slide(slide))
            nav_items.append(("content", heading))

    nav_html = _render_navigator(nav_items)
    all_slides = "\n\n".join(slides_html)

    return _TEMPLATE.format(
        title=title,
        speaker=speaker,
        date=date,
        slides=all_slides,
        navigator=nav_html,
        total_slides=len(slides_data.get("slides", [])),
    )


# ------------------------------------------------------------------
# Slide renderers
# ------------------------------------------------------------------


def _render_title_slide(slide: dict, badge_label: str, badge_gradient: str) -> str:
    heading = _esc(slide.get("heading", ""))
    subtitle = _esc(slide.get("subtitle", ""))
    meta = _esc(slide.get("meta", ""))
    return f"""\
            <section data-background-gradient="radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a12 100%)">
                <div class="light-rays"></div>
                <span class="room-badge" style="background: {badge_gradient};">{badge_label}</span>
                <h1>{heading}</h1>
                <p class="subtitle">{subtitle}</p>
                <p style="font-size: 0.8em; color: var(--text-muted);">{meta}</p>
            </section>"""


def _render_scripture_slide(slide: dict) -> str:
    heading = _esc(slide.get("heading", ""))
    text = _esc(slide.get("scripture_text", ""))
    ref = _esc(slide.get("scripture_ref", ""))
    points = slide.get("points", [])
    points_html = "".join(
        f'\n                        <li class="fragment fade-up">{_esc(p)}</li>'
        for p in points
    )
    points_block = ""
    if points:
        points_block = f"""
                    <ul class="prayer-list">{points_html}
                    </ul>"""
    return f"""\
            <section data-auto-animate>
                <h2>{heading}</h2>
                <div class="scripture-glass">
                    <p class="scripture-text">"{text}"</p>
                    <p class="scripture-ref">&mdash; {ref}</p>
                </div>{points_block}
            </section>"""


def _render_content_slide(slide: dict) -> str:
    heading = _esc(slide.get("heading", ""))
    points = slide.get("points", [])
    highlight = slide.get("highlight", "")
    items = "".join(
        f'\n                        <li class="fragment fade-up">{_esc(p)}</li>'
        for p in points
    )
    highlight_html = ""
    if highlight:
        highlight_html = f"""
                    <div class="room-accent fragment fade-in" style="margin-top: 1em;">
                        <p><em>{_esc(highlight)}</em></p>
                    </div>"""
    return f"""\
            <section data-auto-animate>
                <h2>{heading}</h2>
                <ul class="prayer-list">{items}
                </ul>{highlight_html}
            </section>"""


def _render_prayer_slide(slide: dict) -> str:
    heading = _esc(slide.get("heading", "Prayer Focus"))
    points = slide.get("points", [])
    items = "".join(
        f'\n                        <li class="fragment fade-up">{_esc(p)}</li>'
        for p in points
    )
    return f"""\
            <section data-background-gradient="radial-gradient(ellipse at center, #1a1a2e 0%, #0f0f1a 100%)">
                <h2 style="color: var(--gold);">{heading}</h2>
                <ul class="prayer-list" style="text-align: left;">{items}
                </ul>
            </section>"""


def _render_application_slide(slide: dict) -> str:
    heading = _esc(slide.get("heading", "Living It Out"))
    points = slide.get("points", [])
    items = "".join(
        f'\n                        <li class="fragment fade-up">{_esc(p)}</li>'
        for p in points
    )
    return f"""\
            <section data-auto-animate>
                <h2>{heading}</h2>
                <ul class="prayer-list">{items}
                </ul>
            </section>"""


def _render_closing_slide(slide: dict) -> str:
    heading = _esc(slide.get("heading", ""))
    text = slide.get("scripture_text", "")
    ref = slide.get("scripture_ref", "")
    cta = slide.get("call_to_action", "")
    scripture_block = ""
    if text:
        scripture_block = f"""
                    <div class="scripture-glass">
                        <p class="scripture-text">"{_esc(text)}"</p>
                        <p class="scripture-ref">&mdash; {_esc(ref)}</p>
                    </div>"""
    cta_block = ""
    if cta:
        cta_block = f"""
                    <p class="fragment fade-in" style="margin-top: 1.5em; font-size: 1.1em; color: var(--gold-light);">
                        {_esc(cta)}
                    </p>"""
    return f"""\
            <section data-background-gradient="radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a12 100%)">
                <div class="light-rays"></div>
                <h2 style="color: var(--gold);">{heading}</h2>{scripture_block}{cta_block}
            </section>"""


def _render_navigator(items: list[tuple[str, str]]) -> str:
    """Build the slide navigator grid items."""
    icons = {
        "title": "&#9733;",
        "scripture": "&#128214;",
        "content": "&#128221;",
        "prayer": "&#128591;",
        "application": "&#128161;",
        "closing": "&#10084;",
    }
    nav_items = []
    for i, (stype, label) in enumerate(items):
        icon = icons.get(stype, "&#128221;")
        nav_items.append(
            f'                    <button class="slide-nav-item" data-slide="{i}" '
            f'aria-label="Go to slide {i + 1}: {_esc(label)}">'
            f"{icon} {_esc(label)}</button>"
        )
    return "\n".join(nav_items)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(text)) if text else ""


# ------------------------------------------------------------------
# Full HTML template
# ------------------------------------------------------------------

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {speaker}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
    <link rel="stylesheet" href="../../assets/css/presentation-theme.css">
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to content</a>

    <a href="../../presentations.html" class="home-btn" aria-label="Back to presentations">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
    </a>

    <button class="slide-nav-trigger" aria-label="Open slide navigator (G)"
        onclick="document.querySelector('.slide-navigator').classList.toggle('active')">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <rect x="1" y="1" width="7" height="7" rx="1"/><rect x="12" y="1" width="7" height="7" rx="1"/>
            <rect x="1" y="12" width="7" height="7" rx="1"/><rect x="12" y="12" width="7" height="7" rx="1"/>
        </svg>
    </button>

    <div class="slide-navigator" role="dialog" aria-label="Slide navigator">
        <div class="slide-nav-header">
            <h3>Slides ({total_slides})</h3>
            <button class="slide-nav-close" aria-label="Close navigator"
                onclick="this.closest('.slide-navigator').classList.remove('active')">&times;</button>
        </div>
        <div class="slide-nav-grid">
{navigator}
        </div>
    </div>

    <div class="reveal" id="main-content">
        <div class="slides">
{slides}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: 'c/t',
            controls: true,
            controlsLayout: 'bottom-right',
            progress: true,
            center: true,
            transition: 'slide',
            transitionSpeed: 'default',
            autoAnimateDuration: 0.8,
            width: 960,
            height: 700,
            margin: 0.1,
            minScale: 0.2,
            maxScale: 1.5,
            touch: true,
            keyboard: true,
            fragments: true,
        }});

        // Slide navigator keyboard shortcut
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'g' || e.key === 'G') {{
                document.querySelector('.slide-navigator').classList.toggle('active');
            }}
        }});

        // Slide navigator click handling
        document.querySelectorAll('.slide-nav-item').forEach(function(btn) {{
            btn.addEventListener('click', function() {{
                var idx = parseInt(this.dataset.slide);
                Reveal.slide(idx);
                document.querySelector('.slide-navigator').classList.remove('active');
            }});
        }});
    </script>
</body>
</html>
"""
