import re
from pathlib import Path

from ..findings import Finding, Level
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-bib"
CATEGORY = "references"
LEVEL = "quick"
SKIP_TYPES = {"string", "preamble", "comment"}


def parse_bib(text):
    """Return {key: (entry_type, body)} using brace matching."""
    entries = {}
    for m in re.finditer(r"@(\w+)\s*([{(])\s*([^,\s]+)\s*,", text):
        etype, opener, key = m.group(1).lower(), m.group(2), m.group(3)
        if etype in SKIP_TYPES:
            continue
        closer, depth, i = ("}" if opener == "{" else ")"), 1, m.end()
        while i < len(text) and depth:
            if text[i] == opener:
                depth += 1
            elif text[i] == closer:
                depth -= 1
            i += 1
        entries[key] = (etype, text[m.end():i])
    return entries


def has_doi(body):
    if re.search(r"(?i)(?:^|[,\s])doi\s*=\s*[{\"]?\s*[^\s{}\",]", body):
        return True
    return bool(re.search(r"(?i)\burl\s*=\s*[{\"][^}\"]*doi\.org/", body))


ONLINE_TYPES = {"online", "electronic", "www", "webpage"}


def is_online(etype, body):
    if etype in ONLINE_TYPES:
        return True
    # a @misc with a URL (or \url in howpublished) and no journal/book venue
    has_url = re.search(r"(?i)(?:\burl\s*=|howpublished\s*=\s*[{\"]?\s*\\url)", body)
    venue = re.search(r"(?i)\b(?:journal|booktitle|publisher)\s*=", body)
    return etype == "misc" and bool(has_url) and not venue


def cited_entries(folders):
    """Return ({key: (type, body, bibfile)}, cited_keys, nocite_all) for the given folders."""
    alltext = "\n".join(strip_comments(read(f)) for f in tex_files(folders))
    cited, nocite_all = set(), False
    for m in re.finditer(r"\\(nocite|\w*cite\w*)(?:\[[^\]]*\])*\{([^}]+)\}", alltext):
        for key in m.group(2).split(","):
            key = key.strip()
            if key == "*" and m.group(1) == "nocite":
                nocite_all = True
            else:
                cited.add(key)
    entries = {}
    for folder in folders:
        for b in Path(folder).rglob("*.bib"):
            for key, (etype, body) in parse_bib(read(b)).items():
                entries.setdefault(key, (etype, body, b))
    return entries, cited, nocite_all


def check(folders, config):
    out = []
    entries, cited, nocite_all = cited_entries(folders)
    if not entries:
        return out
    checked = 0
    for key, (etype, body, b) in sorted(entries.items()):
        if key in cited or nocite_all:
            checked += 1
            if not has_doi(body) and not is_online(etype, body):
                out.append(Finding(Level.WARNING, NAME, str(b), f"Cited entry '{key}' ({etype}) has no DOI"))
    out.append(Finding(Level.INFO, NAME, str(folders[0]), f"Checked DOIs for {checked} cited bib entr{'y' if checked == 1 else 'ies'}"))
    return out


