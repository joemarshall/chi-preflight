from PyPDF2 import PdfReader

from ..findings import Finding, Level
from ._banned import find_banned

NAME = "pdf-banned-text"
CATEGORY = "content"
LEVEL = "quick"


def check(path, config):
    banned = config.get("banned_text")
    if not banned:
        return []
    r = PdfReader(path)
    if r.is_encrypted:
        return []
    out = []
    for i, page in enumerate(r.pages, 1):
        for phrase, message in find_banned(page.extract_text() or "", banned):
            out.append(Finding(Level.ERROR, NAME, f"{path} p{i}", f"{message} (found: '{phrase}')"))
    return out
