from docx import Document

from ..findings import Finding, Level

NAME = "docx-metadata"


def check(path, config):
    out = []
    p = Document(path).core_properties
    if not (p.title or "").strip():
        out.append(Finding(Level.WARNING, NAME, path, "Document title property is empty"))
    return out

