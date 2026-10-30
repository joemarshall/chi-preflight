from PyPDF2 import PdfReader

from ..findings import Finding, Level
from . import _doi

NAME = "pdf-dois"
CATEGORY = "references"


def check(path, config):
    r = PdfReader(path)
    if r.is_encrypted:
        return []
    locs = {}
    for i, page in enumerate(r.pages, 1):
        texts = [page.extract_text() or ""]
        for a in page.get("/Annots") or []:
            try:
                act = a.get_object().get("/A")
                uri = act.get_object().get("/URI") if act is not None else None
            except Exception:
                continue
            if uri:
                texts.append(str(uri))
        for d in _doi.extract_dois(" ".join(texts)):
            locs.setdefault(d, set()).add(f"{path} p{i}")
    return _doi.findings(locs, config, NAME, CATEGORY, Finding, Level)
