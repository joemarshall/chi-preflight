import re

from docx import Document

from ..findings import Finding, Level

NAME = "docx-abstract"
CATEGORY = "length"
ABSTRACT_RE = re.compile(r"(?:\d+\.?\s*)?abstract:?", re.I)
# ends the abstract even when the template doesn't mark headings with a heading style
SECTION_RE = re.compile(r"(?:\d+\.?\s*)?(?:keywords?|ccs concepts|acm reference format|introduction)(?:\s*:.*)?", re.I)


def _is_heading(p):
    return p.style.name.lower().startswith(("heading", "title"))


def check(path, config):
    limit = config.get("max_abstract_words")
    if not limit:
        return []
    paras = Document(path).paragraphs
    start = next((i for i, p in enumerate(paras) if ABSTRACT_RE.fullmatch(p.text.strip())), None)
    if start is None:
        return [Finding(Level.WARNING, NAME, path, 'No "Abstract" heading found')]
    words = 0
    for p in paras[start + 1:]:
        text = p.text.strip()
        if not text:
            continue
        if _is_heading(p) or SECTION_RE.fullmatch(text):
            break
        words += len(text.split())
    out = [Finding(Level.INFO, NAME, path, f"Abstract word count: {words} (maximum {limit})")]
    if words == 0:
        out.append(Finding(Level.WARNING, NAME, path, "Abstract section is empty"))
    elif words > limit:
        out.append(Finding(Level.ERROR, NAME, path, f"Abstract has {words} words, exceeding maximum of {limit}"))
    return out
