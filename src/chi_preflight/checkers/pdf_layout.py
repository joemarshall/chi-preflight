from PyPDF2 import PdfReader

from ..findings import Finding, Level

NAME = "pdf-layout"


def check(path, config):
    out = []
    r = PdfReader(path)
    n = len(r.pages)
    out.append(Finding(Level.INFO, NAME, path, f"{n} page(s)"))
    if n == 0:
        out.append(Finding(Level.ERROR, NAME, path, "PDF has no pages"))
        return out
    sizes = {(round(float(p.mediabox.width)), round(float(p.mediabox.height))) for p in r.pages}
    if len(sizes) > 1:
        out.append(Finding(Level.WARNING, NAME, path, f"Mixed page sizes: {sorted(sizes)}"))
    known = {(612, 792): "US Letter", (595, 842): "A4"}
    for s in sizes:
        if s not in known and (s[1], s[0]) not in known:
            out.append(Finding(Level.WARNING, NAME, path, f"Non-standard page size {s[0]}x{s[1]} pt"))
    return out

