import re

from PyPDF2 import PdfReader

from ..findings import Finding, Level

NAME = "pdf-content"
CATEGORY = "content"
LEVEL = "quick"


def check(path, config):
    out = []
    r = PdfReader(path)
    empty = []
    for i, page in enumerate(r.pages, 1):
        text = page.extract_text() or ""
        if not text.strip():
            empty.append(i)
        if "??" in text:
            out.append(Finding(Level.WARNING, NAME, f"{path} p{i}", "Literal '??' (unresolved reference?)"))
        if re.search(r"\b(TODO|FIXME)\b", text):
            out.append(Finding(Level.WARNING, NAME, f"{path} p{i}", "TODO/FIXME marker"))
    if empty:
        out.append(Finding(Level.WARNING, NAME, path, f"No extractable text on page(s): {empty}"))
    return out

