import re

from ..findings import Finding
from . import _reflinks
from .latex_bib import cited_entries, has_doi

NAME = "latex-ref-links"
CATEGORY = "references"
LEVEL = "full"


def _field(body, name):
    m = re.search(r"(?i)(?:^|[,\s])%s\s*=\s*" % name, body)
    if not m:
        return None
    i = m.end()
    if i >= len(body):
        return None
    if body[i] == "{":
        depth, j = 1, i + 1
        while j < len(body) and depth:
            depth += (body[j] == "{") - (body[j] == "}")
            j += 1
        return body[i + 1:j - 1]
    if body[i] == '"':
        j = body.find('"', i + 1)
        return body[i + 1:j] if j > 0 else None
    return re.match(r"[^,\s]*", body[i:]).group(0)


def _clean_title(t):
    t = re.sub(r"\\[a-zA-Z]+\*?\s*(?=\{)", "", t)  # \emph{x} -> {x}
    t = re.sub(r"\\[`'^\"~=.]\{?(\w)\}?", r"\1", t)
    t = t.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
    t = re.sub(r"[{}]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _url(body):
    u = _field(body, "url")
    if not u:
        h = _field(body, "howpublished") or ""
        m = re.search(r"\\url\{([^}]+)\}|(https?://\S+)", h)
        u = (m.group(1) or m.group(2)) if m else None
    if u:
        u = u.replace("\\_", "_").replace("\\%", "%").replace("\\&", "&").strip()
        u = re.sub(r"\\url\{(.*)\}", r"\1", u)
    return u or None


def check(folders, config):
    entries, cited, nocite_all = cited_entries(folders)
    refs = []
    for key, (etype, body, b) in sorted(entries.items()):
        if (key in cited or nocite_all) and not has_doi(body):
            t = _field(body, "title")
            refs.append({"label": f"'{key}'", "location": str(b), "url": _url(body),
                         "title": _clean_title(t) if t else None})
    return _reflinks.findings(refs, config, NAME, CATEGORY)
