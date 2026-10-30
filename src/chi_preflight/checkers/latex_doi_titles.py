from . import _crossref, _doi
from .latex_bib import cited_entries
from .latex_ref_links import _clean_title, _field

NAME = "latex-doi-titles"
CATEGORY = "references"


def check(folders, config):
    entries, cited, nocite_all = cited_entries(folders)
    items = []
    for key, (etype, body, b) in sorted(entries.items()):
        if not (key in cited or nocite_all):
            continue
        title = _field(body, "title")
        if not title:
            continue
        dois = _doi.extract_dois((_field(body, "doi") or "") + " " + (_field(body, "url") or ""))
        if dois:
            items.append({"doi": sorted(dois)[0], "label": f"'{key}'", "location": str(b), "title": _clean_title(title)})
    return _crossref.findings(items, config, NAME, CATEGORY,
                              lambda i, official: _crossref.title_similarity(i["title"], official))
