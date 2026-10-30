import re

from docx import Document

from ..findings import Finding, Level

NAME = "docx-abstract"
CATEGORY = "length"
LEVEL = "quick"
ABSTRACT_RE = re.compile(r"(?:\d+\.?\s*)?abstract:?", re.I)
# ends the abstract even when the template doesn't mark headings with a heading style
SECTION_RE = re.compile(r"(?:\d+\.?\s*)?(?:keywords?|ccs concepts|acm reference format|introduction)(?:\s*:.*)?", re.I)


def _is_heading(p):
    return p.style.name.lower().startswith(("heading", "title"))


def check(path, config):
    limit = config.get("max_abstract_words")
    minimum = config.get("min_abstract_words")
    if not limit and not minimum:
        return []
    paras = Document(path).paragraphs
    style = config.get("abstract_style")
    words = 0
    if style:
        entries = [p for p in paras if p.style.name.lower() == style.lower() and p.text.strip()]
        if not entries:
            return [Finding(Level.ERROR, NAME, path, f'No abstract found: no paragraphs in style "{style}"')]
        words = sum(len(p.text.split()) for p in entries)
    else:
        start = next((i for i, p in enumerate(paras) if ABSTRACT_RE.fullmatch(p.text.strip())), None)
        if start is None:
            return [Finding(Level.ERROR, NAME, path, 'No abstract found: no "Abstract" heading')]
        for p in paras[start + 1:]:
            text = p.text.strip()
            if not text:
                continue
            if _is_heading(p) or SECTION_RE.fullmatch(text):
                break
            words += len(text.split())
    out = [Finding(Level.INFO, NAME, path, f"Abstract word count: {words} (minimum {minimum or 0}, maximum {limit or 'none'})")]
    if minimum and words < minimum:
        out.append(Finding(Level.ERROR, NAME, path, f"Abstract has only {words} words, fewer than minimum of {minimum}"))
    if limit and words > limit:
        out.append(Finding(Level.ERROR, NAME, path, f"Abstract has {words} words, exceeding maximum of {limit}"))
    return out
