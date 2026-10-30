import re

from docx import Document

from ..findings import Finding, Level

NAME = "docx-bibliography"
DOI_RE = re.compile(r"(?i)\b10\.\d{4,9}/\S+|doi\.org/|\bdoi\s*:")


def _is_heading(p):
    return p.style.name.lower().startswith(("heading", "title"))


def _link_targets(p):
    rels = p.part.rels
    ids = p._p.xpath(".//w:hyperlink/@r:id")
    return " ".join(rels[i].target_ref for i in ids if i in rels)


def check(path, config):
    doc = Document(path)
    paras = doc.paragraphs
    start = next((i for i, p in enumerate(paras)
                  if re.fullmatch(r"(?:\d+\.?\s*)?bibliography:?", p.text.strip(), re.I)), None)
    if start is None:
        return [Finding(Level.ERROR, NAME, path, 'No "Bibliography" section found')]
    out = []
    count = 0
    for p in paras[start + 1:]:
        if _is_heading(p):
            break
        text = p.text.strip()
        if not text:
            continue
        count += 1
        if not DOI_RE.search(text + " " + _link_targets(p)):
            out.append(Finding(Level.WARNING, NAME, path, f"Reference has no DOI: {text}"))
    if count == 0:
        out.append(Finding(Level.WARNING, NAME, path, "Bibliography section is empty"))
    else:
        out.append(Finding(Level.INFO, NAME, path, f"Checked DOIs for {count} reference entr{'y' if count == 1 else 'ies'}"))
    return out

