import re

from docx import Document

from ..findings import Finding, Level

NAME = "docx-content"


def check(path, config):
    out = []
    doc = Document(path)
    for i, p in enumerate(doc.paragraphs, 1):
        t = p.text
        if re.search(r"\b(TODO|FIXME|XXX)\b", t):
            out.append(Finding(Level.WARNING, NAME, f"{path} para {i}", "TODO/FIXME marker"))
        if "??" in t:
            out.append(Finding(Level.WARNING, NAME, f"{path} para {i}", "Literal '??' (broken reference?)"))
        if "  " in t.strip():
            out.append(Finding(Level.INFO, NAME, f"{path} para {i}", "Double space"))
    xml = doc.element.xml
    if "<w:ins " in xml or "<w:del " in xml:
        out.append(Finding(Level.WARNING, NAME, path, "Tracked changes present"))
    if "w:commentReference" in xml:
        out.append(Finding(Level.WARNING, NAME, path, "Comments present"))
    return out

