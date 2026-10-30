import re

from docx import Document

from . import _reflinks
from .docx_bibliography import DOI_RE, _is_heading, _link_targets
import re as _re

NAME = "docx-ref-links"
CATEGORY = "references"
LEVEL = "full"
URL_RE = re.compile(r"https?://[^\s<>\"]+", re.I)
TITLE_RES = [
    re.compile(r"[\"\u201c]([^\"\u201d]{8,}?)[,.]?[\"\u201d]"),  # quoted title
    re.compile(r"\b(?:19|20)\d{2}[a-z]?\.\s+(.+?[.?!])\s"),  # ACM: Authors. Year. Title. Venue.
]


def _title(text):
    for rx in TITLE_RES:
        m = rx.search(text)
        if m:
            return m.group(1).strip().rstrip(".")
    return None


def check(path, config):
    doc = Document(path)
    paras = doc.paragraphs
    heading = config["bibliography_heading"]
    pattern = r"(?:\d+\.?\s*)?%s:?" % re.escape(heading)
    start = next((i for i, p in enumerate(paras) if re.fullmatch(pattern, p.text.strip(), re.I)), None)
    if start is None:
        return []
    style = config.get("bibliography_style")
    refs = []
    for p in paras[start + 1:]:
        if _is_heading(p):
            break
        text = p.text.strip()
        if not text:
            continue
        if style and p.style.name.lower() != style.lower():
            break
        links = _link_targets(p)
        if DOI_RE.search(text + " " + links):
            continue
        m = URL_RE.search(links) or URL_RE.search(text)
        url = m.group(0).rstrip(".,;)") if m else None
        refs.append({"label": text[:120], "location": path, "url": url, "title": _title(text)})
    return _reflinks.findings(refs, config, NAME, CATEGORY)
