import re

from PyPDF2 import PdfReader

from ..findings import Finding, Level

NAME = "pdf-authors"
ORCID_RE = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dXx]\b")


def _annotations(reader):
    for i, page in enumerate(reader.pages, 1):
        for a in page.get("/Annots") or []:
            try:
                yield i, a.get_object()
            except Exception:
                continue


def check(path, config):
    anon = config.get("anonymous", True)
    r = PdfReader(path)
    if r.is_encrypted:
        return []
    out = []
    meta = r.metadata
    author = ((meta.author if meta else "") or "").strip()
    xmp_creators = []
    try:
        x = r.xmp_metadata
        if x and x.dc_creator:
            xmp_creators = [c for c in x.dc_creator if str(c).strip()]
    except Exception:
        pass
    links, annot_authors = [], set()
    for page_no, a in _annotations(r):
        t = a.get("/T")
        if t and str(t).strip():
            annot_authors.add(str(t))
        act = a.get("/A")
        if act is not None:
            uri = act.get_object().get("/URI")
            if uri:
                links.append(str(uri))
    text = " ".join((p.extract_text() or "") for p in r.pages)
    orcids = set(ORCID_RE.findall(text)) | {m for u in links for m in ORCID_RE.findall(u)}
    orcids_linked = {m for u in links if "orcid.org" in u for m in ORCID_RE.findall(u)}
    if anon:
        if author:
            out.append(Finding(Level.ERROR, NAME, path, f"Author metadata present: {author!r}"))
        for c in xmp_creators:
            out.append(Finding(Level.ERROR, NAME, path, f"XMP creator metadata present: {c!r}"))
        for a in sorted(annot_authors):
            out.append(Finding(Level.ERROR, NAME, path, f"PDF comment/annotation author present: {a!r}"))
        if orcids or any("orcid.org" in u for u in links):
            out.append(Finding(Level.ERROR, NAME, path, "ORCID found in PDF"))
        first = r.pages[0].extract_text() if len(r.pages) else ""
        for e in sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", first or ""))):
            out.append(Finding(Level.ERROR, NAME, path, f"Email address on first page: {e}"))
    else:
        if not author and not xmp_creators:
            out.append(Finding(Level.ERROR, NAME, path, "Author metadata is missing"))
            return out
        names = author or "; ".join(map(str, xmp_creators))
        n_auth = len([a for a in re.split(r"[;,]|\band\b", names) if a.strip()])
        if not orcids_linked:
            out.append(Finding(Level.WARNING, NAME, path, "No linked ORCID iDs (orcid.org links) found"))
        elif len(orcids_linked) < n_auth:
            out.append(Finding(Level.WARNING, NAME, path, f"{len(orcids_linked)} linked ORCID iD(s) for {n_auth} author(s)"))
        out.append(Finding(Level.INFO, NAME, path, f"Author metadata: {names!r}; {len(orcids_linked)} linked ORCID iD(s)"))
    return out

