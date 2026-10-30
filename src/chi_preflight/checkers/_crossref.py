"""Compare titles against the Crossref (or, failing that, DataCite) record of a DOI."""
import html
import re
import time
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from urllib.parse import quote

import requests

from ..findings import Finding, Level

HEADERS = {"User-Agent": "chi-preflight (title check; https://github.com/)"}
_cache = {}


def _norm(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"[\W_]+", " ", text.lower()).strip()


def _crossref(doi):
    r = requests.get("https://api.crossref.org/works/" + quote(doi, safe="/:()"), headers=HEADERS, timeout=25)
    if r.status_code == 404:
        return ("missing", "not registered with Crossref")
    if r.status_code != 200:
        return ("unknown", f"HTTP {r.status_code}")
    msg = r.json()["message"]
    title = " ".join(msg.get("title") or [])
    sub = " ".join(msg.get("subtitle") or [])
    if not title:
        return ("missing", "Crossref record has no title")
    return ("ok", f"{title}: {sub}" if sub and sub.lower() not in title.lower() else title)


def _datacite(doi):
    r = requests.get("https://api.datacite.org/dois/" + quote(doi, safe="/:()"), headers=HEADERS, timeout=25)
    if r.status_code == 404:
        return ("missing", "not registered with Crossref or DataCite")
    if r.status_code != 200:
        return ("unknown", f"HTTP {r.status_code}")
    titles = [t.get("title", "") for t in r.json()["data"]["attributes"].get("titles") or []]
    titles = [t for t in titles if t]
    return ("ok", titles[0]) if titles else ("missing", "DataCite record has no title")


def crossref_title(doi):
    """Return (status, title_or_detail): ok / missing (in neither registry) / unknown."""
    if doi in _cache:
        return _cache[doi]
    res = ("unknown", "no response")
    for attempt in range(3):
        try:
            res = _crossref(doi)
            if res[0] == "missing":
                res = _datacite(doi)
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            res = ("unknown", f"{type(e).__name__}")
        if res[0] != "unknown":
            break
        time.sleep(1 + attempt)
    _cache[doi] = res
    return res


def lookup_all(dois):
    dois = list(dois)
    with ThreadPoolExecutor(max_workers=6) as pool:
        return dict(zip(dois, pool.map(crossref_title, dois)))


def title_similarity(given, official):
    """0..1: how well a document title matches the Crossref title (the title may be a prefix of it)."""
    a, b = _norm(given), _norm(official)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def text_contains_title(text, official):
    """0..1: fraction of the official title's words found in a reference's free text."""
    words = _norm(official).split()
    have = set(_norm(text).split())
    return sum(w in have for w in words) / len(words) if words else 0.0


def findings(items, config, name, category, scorer, threshold=0.8):
    """items: list of {doi, label, location, ...}. scorer(item, official_title) -> 0..1."""
    if not items:
        return []
    if not config.get("check_doi_titles", True):
        return [Finding(Level.INFO, name, "-", "DOI title checks disabled", category)]
    results = lookup_all({i["doi"] for i in items})
    out, checked, skipped, unknown = [], 0, 0, 0
    for i in items:
        status, detail = results[i["doi"]]
        if status == "unknown":
            unknown += 1
        elif status == "missing":
            skipped += 1
        else:
            checked += 1
            score = scorer(i, detail)
            if score < threshold:
                out.append(Finding(Level.WARNING, name, i["location"],
                                   f'Title does not match DOI {i["doi"]} for {i["label"]}: '
                                   f'the registry has "{detail}" (match {score:.0%})', category))
    if unknown:
        out.append(Finding(Level.WARNING, name, "-", f"Crossref/DataCite was unreachable for {unknown} DOI(s); titles not checked", category))
    msg = f"Compared titles with Crossref/DataCite for {checked} DOI(s)"
    if skipped:
        msg += f" ({skipped} in neither registry, skipped)"
    out.append(Finding(Level.INFO, name, "-", msg, category))
    return out
