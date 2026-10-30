import re

from docx import Document

from . import _crossref, _doi
from .docx_bibliography import _is_heading, _link_targets

NAME = "docx-doi-titles"
CATEGORY = "references"


def check(path, config):
    doc = Document(path)
    paras = doc.paragraphs
    pattern = r"(?:\d+\.?\s*)?%s:?" % re.escape(config["bibliography_heading"])
    start = next((i for i, p in enumerate(paras) if re.fullmatch(pattern, p.text.strip(), re.I)), None)
    if start is None:
        return []
    style = config.get("bibliography_style")
    items = []
    for p in paras[start + 1:]:
        if _is_heading(p):
            break
        text = p.text.strip()
        if not text:
            continue
        if style and p.style.name.lower() != style.lower():
            break
        dois = _doi.extract_dois(text + " " + _link_targets(p))
        if dois:
            items.append({"doi": sorted(dois)[0], "label": text[:120], "location": path, "text": text})
    return _crossref.findings(items, config, NAME, CATEGORY,
                              lambda i, official: _crossref.text_contains_title(i["text"], official))
