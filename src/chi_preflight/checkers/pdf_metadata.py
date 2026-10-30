from PyPDF2 import PdfReader

from ..findings import Finding, Level

NAME = "pdf-metadata"
CATEGORY = "metadata"


def check(path, config):
    out = []
    r = PdfReader(path)
    if r.is_encrypted:
        out.append(Finding(Level.ERROR, NAME, path, "PDF is encrypted"))
        return out
    m = r.metadata
    if not m or not (m.title or "").strip():
        out.append(Finding(Level.WARNING, NAME, path, "Title metadata is empty"))
    if m and m.producer:
        out.append(Finding(Level.INFO, NAME, path, f"Producer: {m.producer}"))
    return out

