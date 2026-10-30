from docx import Document

from ..findings import Finding, Level
from . import _doi
from .docx_banned_text import _paragraphs

NAME = "docx-dois"
CATEGORY = "references"


def check(path, config):
    doc = Document(path)
    locs = {}
    for p in _paragraphs(doc):
        ids = p._p.xpath(".//w:hyperlink/@r:id")
        targets = " ".join(p.part.rels[i].target_ref for i in ids if i in p.part.rels)
        for d in _doi.extract_dois(p.text + " " + targets):
            locs.setdefault(d, set()).add(path)
    return _doi.findings(locs, config, NAME, CATEGORY, Finding, Level)
