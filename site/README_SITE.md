# Trusting Jesus Static Site

A small static website to browse weekly prayer points, sermon summaries, transcripts, and presentations.

## What it does

- Lists content from this repository
- Uses accessible HTML/CSS (WCAG AA), skip link, visible focus, reduced motion
- No build step required; uses pre-generated JSON catalogs

## Generate catalogs

The listing pages read JSON files from `site/data/`. Generate them with the helper script:

1. Ensure you run from the project root folder that contains `prayer_trusting_Jesus/`.
2. Run the script:

```bash
python3 prayer_trusting_Jesus/tools/build_catalog.py
```

This writes:

- `prayer_trusting_Jesus/site/data/prayer_points.json`
- `prayer_trusting_Jesus/site/data/sermons.json`
- `prayer_trusting_Jesus/site/data/transcripts.json`
- `prayer_trusting_Jesus/site/data/presentations.json`

If you add new content, re-run the script.

## View locally

Open `prayer_trusting_Jesus/site/index.html` in your browser. For the best experience, serve it over a local server to avoid CORS issues with `fetch`:

- Python 3 (from repository root):

  ```bash
  cd prayer_trusting_Jesus/site
  python3 -m http.server 8080
  ```

  Then open <http://localhost:8080/> in your browser.

## Add new content

- Weekly prayer points: place markdown files under `prayer_trusting_Jesus/prayer_points/<YEAR>/` using the `templates/weekly_prayer_points_template.md` front matter.
- Sermon summaries: put markdown files in `prayer_trusting_Jesus/sermons_summaries/` using the `templates/sermon_summary_template.md` front matter.
- Transcripts: add new folders under `prayer_trusting_Jesus/transcripts/sermon/<SERMON_NAME>/` with `transcript.md` inside.
- Presentations: add HTML files under `prayer_trusting_Jesus/presentations/`.

After changes, regenerate catalogs.

## Accessibility notes

- Visible focus outlines for keyboard users
- Skip link to bypass repeated navigation
- Color contrast meets WCAG AA on dark backgrounds
- Reduced motion respected via `prefers-reduced-motion`

