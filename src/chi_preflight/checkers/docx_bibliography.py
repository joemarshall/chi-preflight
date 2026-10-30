import re

from docx import Document

from ..findings import Finding, Level

NAME = "docx-bibliography"
CATEGORY = "references"
DOI_RE = re.compile(r"(?i)\b10\.\d{4,9}/\S+|doi\.org/|\bdoi\s*:")


ONLINE_RE = re.compile(r"(?i)https?://|www\.|\b(?:retrieved|accessed)\b")


def _is_heading(p):
    return p.style.name.lower().startswith(("heading", "title"))


def _link_targets(p):
    rels = p.part.rels
    ids = p._p.xpath(".//w:hyperlink/@r:id")
    return " ".join(rels[i].target_ref for i in ids if i in rels)


def check(path, config):
    doc = Document(path)
    paras = doc.paragraphs
    heading = config["bibliography_heading"]
    pattern = r"(?:\d+\.?\s*)?%s:?" % re.escape(heading)
    start = next((i for i, p in enumerate(paras) if re.fullmatch(pattern, p.text.strip(), re.I)), None)
    if start is None:
        return [Finding(Level.ERROR, NAME, path, f'No "{heading}" section found')]
    out = []
    count = online = 0
    style = config.get("bibliography_style")
    if style and not any(st.name.lower() == style.lower() for st in doc.styles):
        out.append(Finding(Level.WARNING, NAME, path, f'Paragraph style "{style}" is not defined in the document'))
    # the section runs until the next heading or the first non-entry paragraph
    for p in paras[start + 1:]:
        if _is_heading(p):
            break
        text = p.text.strip()
        if not text:
            continue
        if style and p.style.name.lower() != style.lower():
            break  # the first non-empty paragraph outside the entry style ends the bibliography
        count += 1
        links = _link_targets(p)
        if DOI_RE.search(text + " " + links):
            continue
        if ONLINE_RE.search(text + " " + links):
            online += 1
        else:
            out.append(Finding(Level.WARNING, NAME, path, f"Reference has no DOI: {text}"))
    if count == 0:
        out.append(Finding(Level.WARNING, NAME, path, "Bibliography section has no reference entries"))
    else:
        out.append(Finding(Level.INFO, NAME, path, f"Checked DOIs for {count} reference entr{'y' if count == 1 else 'ies'} ({online} online, DOI not required)"))
    return out
