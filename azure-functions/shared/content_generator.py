"""Generate sermon content (summary, prayer points, presentation slides) via LLM.

Uses the provider-agnostic LLMClient. All output follows the project's
existing templates and YAML front-matter conventions.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from .llm_client import LLMClient

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Sermon Summary
# ------------------------------------------------------------------

SUMMARY_SYSTEM_PROMPT = """\
You are a ministry assistant producing sermon summaries.
Output a Markdown document with YAML front matter matching this exact structure:

---
title: "<Sermon Title>"
speaker: "<Speaker Name>"
location: "<Church Name>"
date: "<YYYY-MM-DD>"
series: "<Series Name>"
tags: [tag1, tag2, tag3]
scriptures:
  - "<Book Chapter:Verse>"
version: "1.0"
---

## Big Idea
One-sentence thesis of the sermon.

## Outline
### 1. First Main Point
- Supporting detail
- Supporting detail

### 2. Second Main Point
- Supporting detail

(Continue for all main points)

## Key Scriptures
| Scripture | Theme |
|-----------|-------|
| Reference | Brief theme |

## Applications
1. Practical application point
2. Another application

## Prayer Points
1. Prayer based on the sermon
2. Another prayer point

## Call to Respond
Closing invitation/challenge from the sermon.

Rules:
- Pull scripture references DIRECTLY from the transcript
- Use the speaker's own words and phrases where impactful
- Keep the summary thorough but scannable
- Include ALL main points from the sermon
- Tags should be lowercase, relevant theological themes
"""


def generate_summary(
    llm: LLMClient,
    transcript: str,
    metadata: dict,
) -> str:
    """Generate a sermon summary from a transcript."""
    user_prompt = f"""Sermon Transcript:

Title: {metadata.get('title', 'Unknown')}
Speaker: {metadata.get('speaker', 'Unknown')}
Date: {metadata.get('date', 'Unknown')}
Series: {metadata.get('series', '')}

---
{transcript}
---

Generate a complete sermon summary following the template structure exactly."""

    logger.info("Generating sermon summary for: %s", metadata.get("title"))
    return llm.generate(SUMMARY_SYSTEM_PROMPT, user_prompt, max_tokens=4096)


# ------------------------------------------------------------------
# Prayer Points
# ------------------------------------------------------------------

PRAYER_SYSTEM_PROMPT = """\
You are a prayer ministry coordinator creating weekly prayer points from a sermon.

Output a Markdown document with YAML front matter matching this exact structure:

---
week_of: "<YYYY-MM-DD>"
theme: "<Theme from the sermon>"
scriptures:
  - "<Book Chapter:Verse>"
version: "1.0"
---

# Weekly Prayer Points: <Theme>
*Based on: "<Sermon Title>" by <Speaker>*

## Focus Areas

### 1. <Focus Area Title>
**Scripture**: <Reference>
- Prayer point with specific scriptural basis
- Another prayer point

### 2. <Focus Area Title>
**Scripture**: <Reference>
- Prayer point
- Prayer point

(6-8 focus areas total)

## Intercession
- Prayer for the church community
- Prayer for leaders
- Prayer for families

## Declarations
- Faith declaration based on scripture
- Another declaration

## Closing Prayer
A comprehensive closing prayer incorporating the sermon's themes.

Rules:
- ALWAYS include relevant Bible verses from the sermon
- Prayers should be specific, not generic
- Each focus area should have a clear scripture anchor
- Use active, faith-filled language
- Include 6-8 focus areas minimum
"""


def generate_prayer_points(
    llm: LLMClient,
    transcript: str,
    summary: str,
    metadata: dict,
) -> str:
    """Generate weekly prayer points from a sermon."""
    user_prompt = f"""Sermon: "{metadata.get('title', '')}" by {metadata.get('speaker', '')}
Date: {metadata.get('date', '')}

Sermon Summary:
{summary}

Full Transcript (for scripture references):
{transcript[:8000]}

Generate comprehensive prayer points following the template structure exactly."""

    logger.info("Generating prayer points for: %s", metadata.get("title"))
    return llm.generate(PRAYER_SYSTEM_PROMPT, user_prompt, max_tokens=4096)


# ------------------------------------------------------------------
# Presentation Slides (JSON structure -> rendered by template_engine)
# ------------------------------------------------------------------

SLIDES_SYSTEM_PROMPT = """\
You are creating slide content for a Reveal.js church presentation.
Return a JSON object with this exact schema (no markdown fences, pure JSON):

{
  "title": "Sermon Title",
  "speaker": "Speaker Name",
  "date": "Month DD, YYYY",
  "category": "sermon",
  "total_slides": 18,
  "slides": [
    {
      "type": "title",
      "heading": "Sermon Title",
      "subtitle": "Speaker Name",
      "meta": "Church Name | Date"
    },
    {
      "type": "scripture",
      "heading": "Section Title",
      "scripture_text": "Exact quote from the Bible",
      "scripture_ref": "Book Chapter:Verse",
      "points": ["Key insight 1", "Key insight 2"]
    },
    {
      "type": "content",
      "heading": "Main Point Title",
      "points": ["Point with detail", "Another point", "Third point"],
      "highlight": "Optional emphasized phrase"
    },
    {
      "type": "prayer",
      "heading": "Prayer Focus",
      "points": ["Prayer point 1", "Prayer point 2", "Prayer point 3"]
    },
    {
      "type": "application",
      "heading": "Living It Out",
      "points": ["Application 1", "Application 2", "Application 3"]
    },
    {
      "type": "closing",
      "heading": "Closing / Call to Respond",
      "scripture_text": "Closing scripture quote",
      "scripture_ref": "Reference",
      "call_to_action": "Final challenge or invitation"
    }
  ]
}

Rules:
- Create 15-22 slides total
- Start with a title slide and end with a closing slide
- Use 3-5 scripture slides with EXACT Bible quotes
- Each content slide should have 3-5 concise bullet points
- Include at least 2 prayer slides
- Include at least 1 application slide
- Points should be concise (under 15 words each)
- Use the speaker's memorable phrases
- Return ONLY valid JSON, no other text
"""


def generate_slides_json(
    llm: LLMClient,
    transcript: str,
    summary: str,
    metadata: dict,
) -> dict:
    """Generate presentation slide data as structured JSON."""
    user_prompt = f"""Sermon: "{metadata.get('title', '')}" by {metadata.get('speaker', '')}
Date: {metadata.get('date', '')}

Summary:
{summary}

Transcript excerpt (first 6000 chars for context):
{transcript[:6000]}

Generate the slides JSON now. Return ONLY valid JSON."""

    logger.info("Generating presentation slides for: %s", metadata.get("title"))
    return llm.generate_json(SLIDES_SYSTEM_PROMPT, user_prompt, max_tokens=6000)
