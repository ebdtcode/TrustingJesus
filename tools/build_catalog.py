#!/usr/bin/env python3
"""
Build content catalogs for the static site by scanning markdown/html files.
Outputs JSON files under site/data/ with relative paths that work when viewing locally or via GitHub Pages.
No external dependencies.
"""
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / 'site'
SITE_DATA = SITE_DIR / 'data'
SITE_PRESENTATIONS = SITE_DIR / 'presentations'
SITE_CONTENT = SITE_DIR / 'content'

MD_TITLE_RE = re.compile(r'^title:\s*"?(.+?)"?\s*$', re.IGNORECASE)
MD_SPEAKER_RE = re.compile(r'^speaker:\s*"?(.+?)"?\s*$', re.IGNORECASE)
MD_DATE_RE = re.compile(r'^date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*$', re.IGNORECASE)
MD_THEME_RE = re.compile(r'^theme:\s*"?(.+?)"?\s*$', re.IGNORECASE)
MD_WEEK_RE = re.compile(r'^week_of:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*$', re.IGNORECASE)


def read_front_matter(md_path: Path):
    """Parse simple YAML-like front matter block at top of file delimited by --- lines."""
    title = speaker = date = theme = week_of = None
    try:
        with md_path.open('r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines or not lines[0].strip().startswith('---'):
            return {}
        for line in lines[1:50]:  # read first block
            if line.strip().startswith('---'):
                break
            if m := MD_TITLE_RE.match(line.strip()):
                title = m.group(1)
            elif m := MD_SPEAKER_RE.match(line.strip()):
                speaker = m.group(1)
            elif m := MD_DATE_RE.match(line.strip()):
                date = m.group(1)
            elif m := MD_THEME_RE.match(line.strip()):
                theme = m.group(1)
            elif m := MD_WEEK_RE.match(line.strip()):
                week_of = m.group(1)
        data = {}
        if title: data['title'] = title
        if speaker: data['speaker'] = speaker
        if date: data['date'] = date
        if theme: data['theme'] = theme
        if week_of: data['week_of'] = week_of
        return data
    except Exception:
        return {}


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace(os.sep, '/')


def site_href(path_from_root: str) -> str:
    """Make href that works from inside site/ pages (which live one level below ROOT)."""
    return f"../{path_from_root}"


def build_prayer_points():
    out = []
    base = ROOT / 'prayer_points'
    if not base.exists():
        return out
    for year_dir in sorted(base.iterdir()):
        if not year_dir.is_dir():
            continue
        for md in sorted(year_dir.glob('*.md')):
            fm = read_front_matter(md)
            rel_path = rel(md)
            site_rel = f"content/{rel_path}"
            dest = SITE_DIR / site_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(md, dest)
            except Exception:
                pass
            item = {
                'path': site_rel,
                'title': fm.get('title') or fm.get('theme') or md.stem,
                'week_of': fm.get('week_of'),
            }
            out.append(item)
    return out


def build_sermons():
    out = []
    base = ROOT / 'sermons_summaries'
    if not base.exists():
        return out
    for md in sorted(base.glob('*.md')):
        fm = read_front_matter(md)
        rel_path = rel(md)
        site_rel = f"content/{rel_path}"
        dest = SITE_DIR / site_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(md, dest)
        except Exception:
            pass
        item = {
            'path': site_rel,
            'title': fm.get('title') or md.stem,
            'speaker': fm.get('speaker'),
            'date': fm.get('date'),
        }
        out.append(item)
    return out


def build_transcripts():
    out = []
    base = ROOT / 'transcripts' / 'sermon'
    if not base.exists():
        return out
    for sermon_dir in sorted(base.iterdir()):
        if not sermon_dir.is_dir():
            continue
        transcript = sermon_dir / 'transcript.md'
        # Copy entire sermon folder to site/content
        src_dir_rel = rel(sermon_dir)
        dest_dir = SITE_DIR / f"content/{src_dir_rel}"
        try:
            shutil.copytree(sermon_dir, dest_dir, dirs_exist_ok=True)
        except Exception:
            pass
        fm = read_front_matter(transcript) if transcript.exists() else {}
        item = {
            'path': (f"content/{rel(transcript)}" if transcript.exists() else f"content/{rel(sermon_dir)}"),
            'title': fm.get('title') or sermon_dir.name.replace('_', ' '),
            'speaker': fm.get('speaker'),
            'date': fm.get('date'),
            'folder': sermon_dir.name,
        }
        out.append(item)
    return out


def build_presentations():
    out = []
    base = ROOT / 'presentations'
    if not base.exists():
        return out
    # Ensure site/presentations exists and mirror html files there so links work when serving site/ as docroot
    SITE_PRESENTATIONS.mkdir(parents=True, exist_ok=True)
    for html in sorted(base.glob('*.html')):
        title = html.stem.replace('_', ' ')
        # Copy to site/presentations and link site-relative path
        target = SITE_PRESENTATIONS / html.name
        try:
            shutil.copy2(html, target)
        except Exception:
            pass
        out.append({ 'path': f'presentations/{html.name}', 'title': title, 'meta': '' })
    return out


def main():
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    catalogs = {
        'prayer_points.json': build_prayer_points(),
        'sermons.json': build_sermons(),
        'transcripts.json': build_transcripts(),
        'presentations.json': build_presentations(),
    }
    for name, items in catalogs.items():
        (SITE_DATA / name).write_text(json.dumps(items, indent=2), encoding='utf-8')
    print(f"Wrote catalogs: {', '.join(catalogs.keys())}")

if __name__ == '__main__':
    main()
