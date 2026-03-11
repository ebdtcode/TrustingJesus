# Add New Sermon to Prayer Site

## Description
Add a new sermon from YouTube to the V2 Prayer Trusting Jesus site with the stained glass theme. This command handles the complete workflow from transcription to presentation creation.

## Arguments
- `url` (required): YouTube URL of the sermon to add
- `--skip-transcription`: Skip transcription if transcript already exists
- `--title`: Override the sermon title (default: extracted from YouTube)
- `--speaker`: Override speaker name (default: extracted from YouTube)

## Source URL

$ARGUMENTS

**IMPORTANT:** If no URL or file path is provided above (shows as "$ARGUMENTS" literally or is empty), you MUST ask the user for the YouTube URL or local audio file path before proceeding.

## Workflow

### 1. Validate Input
- Check if a valid URL or file path was provided
- If not, use AskUserQuestion to get the sermon URL/path from the user

### 2. Activate Shared MLX Agents Virtual Environment

Use the shared MLX agents venv (project-independent, managed centrally):

```bash
source "$MLX_AGENTS_HOME/bin/activate"
```

Where `MLX_AGENTS_HOME` is `$HOME/.local/share/mlx-agents`.

**Pre-installed packages**: `mlx-whisper`, `mlx-lm`, `mlx-vlm`, `mlx-audio`, `mflux`, `torch`, `transformers`

**Do NOT** use any project-local venv (e.g., `prayer_trusting_Jesus/venv/`). The shared venv is the single source of truth for all ML tooling.

### 3. Download Audio from YouTube

Use system-installed `yt-dlp` to download audio:

```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "working_docs/sermon_$(date +%Y%m%d).%(ext)s" \
  "YOUTUBE_URL"
```

### 4. Transcribe with MLX Whisper

Use `mlx_whisper` from the shared venv:

```bash
mlx_whisper working_docs/sermon_*.mp3 --model mlx-community/whisper-base-mlx --language en \
  --output-dir working_docs --output-format txt
```

Available models (speed vs accuracy tradeoff):
- `mlx-community/whisper-tiny-mlx` - Fastest, lower accuracy
- `mlx-community/whisper-base-mlx` - Good balance (default)
- `mlx-community/whisper-small-mlx` - Better accuracy
- `mlx-community/whisper-medium-mlx` - High accuracy
- `mlx-community/whisper-large-v3-mlx` - Best accuracy, slowest

**Cleanup after transcription**: Remove the downloaded MP3 from `working_docs/` after the transcript is saved. Do not leave audio files in the working directory.

### 5. Process with Sermon Prayer Generator Agent

Use the **sermon-prayer-generator agent** to:
- Generate sermon summary with key points and scripture references
- Create prayer points based on sermon themes
- Save outputs to `working_docs/` for review

### 6. Create V2 Presentation

#### File Location
Create the presentation in the appropriate category folder:
- Sermons: `site/v2/presentations/sermons/`
- Prayer: `site/v2/presentations/prayer/`
- Personal Development: `site/v2/presentations/personal-development/`
- Marriage: `site/v2/presentations/marriage/`
- Faith: `site/v2/presentations/faith/`
- Family: `site/v2/presentations/family/`

#### Template Structure
Use this V2 stained glass theme template:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="SERMON_DESCRIPTION">
    <title>SERMON_TITLE | SERIES_NAME</title>

    <!-- Reveal.js -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">

    <!-- V2 Presentation Theme -->
    <link rel="stylesheet" href="../../assets/css/presentation-theme.css">
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to content</a>

    <a href="../../presentations.html" class="home-btn" aria-label="Return to presentations list">
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span>Home</span>
    </a>

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

    <div class="reveal" id="main-content">
        <div class="slides">

            <!-- TITLE SLIDE -->
            <section data-background-gradient="radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a12 100%)">
                <div class="light-rays"></div>
                <span class="room-badge" style="background: linear-gradient(135deg, var(--ruby), var(--ruby-dark));">SERIES_NAME</span>
                <h1>SERMON_TITLE</h1>
                <p class="subtitle">SPEAKER_NAME</p>
                <p style="font-size: 0.6em; color: var(--text-muted); margin-top: 1.5em;">SCRIPTURE_REF</p>
            </section>

            <!-- ADD CONTENT SLIDES HERE -->
            <!-- Use these V2 components: -->

            <!-- Scripture Glass Panel -->
            <!--
            <div class="scripture-glass" style="border-left-color: var(--ruby);">
                <p class="scripture-text">"Scripture text here"</p>
                <p class="scripture-ref">Book Chapter:Verse (Version)</p>
            </div>
            -->

            <!-- Prayer Panel -->
            <!--
            <div class="prayer-panel">
                <h4>Prayer Focus</h4>
                <p>Prayer content here</p>
            </div>
            -->

            <!-- Prayer List -->
            <!--
            <ul class="prayer-list">
                <li class="fragment fade-up">Point 1</li>
                <li class="fragment fade-up">Point 2</li>
            </ul>
            -->

            <!-- Colored Accent Boxes (use jewel tone colors) -->
            <!-- var(--ruby), var(--sapphire), var(--emerald), var(--amber), var(--amethyst), var(--gold) -->

        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
    <script src="../../assets/js/presentation.js"></script>
    <script>
        Reveal.initialize({
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

        Reveal.addKeyBinding({ keyCode: 72, key: 'H', description: 'Go home' }, () => {
            window.location.href = '../../presentations.html';
        });
    </script>
</body>
</html>
```

### 7. Update presentations.js

Add the new sermon entry at the TOP of the presentations array (newest first):

```javascript
// File: site/v2/data/presentations.js

{
  title: "SERMON_TITLE",
  speaker: "SPEAKER_NAME",
  description: "SERMON_DESCRIPTION",
  slides: SLIDE_COUNT,
  file: "presentations/CATEGORY/FILENAME.html",
  id: "SERMON_ID",
  category: "sermon",  // or faith, prayer, etc.
  icon: "&#128156;",   // Heart for love series, adjust as needed
  tags: ["tag1", "tag2", "scripture"],
  featured: true,      // Set to true for new sermons
  date: "YYYY-MM-DD"   // Today's date
},
```

### 8. Run Tests
```bash
cd /Users/devos/git/media/prayer_trusting_Jesus/site
npx playwright test
```

All 17 tests should pass.

### 9. Cleanup

After successful completion:
- Remove temporary audio files from `working_docs/`
- Remove temporary transcript text files from `working_docs/`
- Keep final outputs (presentation HTML, summary markdown) in their proper locations

### 10. Commit and Push
```bash
git add site/v2/presentations/CATEGORY/FILENAME.html site/v2/data/presentations.js
git commit -m "feat: Add SERMON_TITLE presentation"
git tag -a vX.X.X -m "VX.X.X: Add SERMON_TITLE"
git push origin main --tags
```

## Requirements
- Keep slides concise (typically 12-20 slides)
- Include speaker name, church (if known), date, scripture references
- Add prayer points slide(s) at the end
- Use the V2 stained glass theme (Reveal.js + presentation-theme.css)
- Mobile-first: base Reveal.js dimensions 960x700

## V2 Theme Color Reference

| Color | Variable | Hex | Use Case |
|-------|----------|-----|----------|
| Ruby | `--ruby` | #c44d56 | Love, passion, important scriptures |
| Sapphire | `--sapphire` | #4d7cc4 | Peace, wisdom, biblical truths |
| Emerald | `--emerald` | #56c44d | Growth, provision, life |
| Amber | `--amber` | #d4a84b | Warning, wisdom, gold references |
| Amethyst | `--amethyst` | #9b59b6 | Royalty, prayer, spiritual |
| Gold | `--gold` | #d4a84b | Highlight, important, divine |

## Example Sermon Slide Types

### Teaching Point Slide
```html
<section>
    <h2>Teaching Point Title</h2>
    <ul class="prayer-list">
        <li class="fragment fade-up">Point one</li>
        <li class="fragment fade-up">Point two</li>
        <li class="fragment fade-up">Point three</li>
    </ul>
</section>
```

### Scripture Focus Slide
```html
<section>
    <h2>Scripture Title</h2>
    <div class="scripture-glass" style="border-left-color: var(--ruby);">
        <p class="scripture-text">"Scripture text here"</p>
        <p class="scripture-ref">Book Chapter:Verse (Version)</p>
    </div>
    <div class="prayer-panel fragment fade-up">
        <h4>Application</h4>
        <p>What this means for us...</p>
    </div>
</section>
```

### Section Transition Slide
```html
<section data-background-gradient="radial-gradient(ellipse at center, #2d1a1f 0%, #0a0a12 100%)">
    <div class="room-accent"></div>
    <span class="room-badge" style="background: linear-gradient(135deg, var(--ruby), var(--ruby-dark));">Part 2</span>
    <h2>Section Title</h2>
    <p class="subtitle">Section subtitle</p>
</section>
```

### Three Reasons/Points Slide
```html
<section>
    <h2>Three Key Points</h2>
    <div style="display: grid; gap: 1em; margin-top: 1em;">
        <div class="fragment fade-up" style="background: rgba(196, 77, 86, 0.15); border-left: 4px solid var(--ruby); padding: 1em; border-radius: 0 8px 8px 0;">
            <strong style="color: #f5b8bc;">1. First Point</strong>
            <p style="margin: 0.5em 0 0; color: var(--text-secondary);">Explanation</p>
        </div>
        <div class="fragment fade-up" style="background: rgba(77, 124, 196, 0.15); border-left: 4px solid var(--sapphire); padding: 1em; border-radius: 0 8px 8px 0;">
            <strong style="color: #a8c8f5;">2. Second Point</strong>
            <p style="margin: 0.5em 0 0; color: var(--text-secondary);">Explanation</p>
        </div>
        <div class="fragment fade-up" style="background: rgba(86, 196, 77, 0.15); border-left: 4px solid var(--emerald); padding: 1em; border-radius: 0 8px 8px 0;">
            <strong style="color: #a8f5b8;">3. Third Point</strong>
            <p style="margin: 0.5em 0 0; color: var(--text-secondary);">Explanation</p>
        </div>
    </div>
</section>
```

**WCAG AA Contrast Note:** Use light tinted colors for titles on dark tinted backgrounds:
- Ruby background: use `#f5b8bc` (light pink)
- Sapphire background: use `#a8c8f5` (light blue)
- Emerald background: use `#a8f5b8` (light green)
- Amber background: use `#f5e0a8` (light gold)
- Amethyst background: use `#d4a8f5` (light purple)
