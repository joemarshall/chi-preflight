import re

from docx import Document

from ..findings import Finding, Level

NAME = "docx-wordcount"
CATEGORY = "length"
LABEL_RE = re.compile(r"(?:figure|fig\.|table|listing|algorithm|equation)\s*\d+", re.I)


def _is_heading(p):
    return p.style.name.lower().startswith(("heading", "title"))


def _is_label(p):
    return p.style.name.lower().startswith("caption") or bool(LABEL_RE.match(p.text.strip()))


def check(path, config):
    # doc.paragraphs covers body paragraphs only: table cells, headers and footers are excluded
    doc = Document(path)
    words = skipped_caps = skipped_tail = 0
    # counting stops at the configured bibliography heading or any appendix heading
    end_re = re.compile(r"(?:\d+\.?\s*|[A-Z]\.?\s+)?(?:%s|appendix|appendices)\b.*" % re.escape(config["bibliography_heading"]), re.I)
    in_tail = False
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        # counting stops for good at the first appendix/bibliography heading
        if _is_heading(p) and end_re.fullmatch(text):
            in_tail = True
        if in_tail:
            skipped_tail += 1
        elif _is_label(p):
            skipped_caps += 1
        else:
            words += len(text.split())
    out = [Finding(Level.INFO, NAME, path,
                   f"Word count: {words} (excluding appendices and bibliography [{skipped_tail} paragraphs], "
                   f"captions/labels [{skipped_caps}], tables, headers and footers)")]
    limit = config.get("max_words")
    if limit and words > limit:
        out.append(Finding(Level.ERROR, NAME, path, f"Word count {words} exceeds maximum of {limit}"))
    return out
