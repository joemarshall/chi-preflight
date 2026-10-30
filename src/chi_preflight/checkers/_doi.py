"""Shared DOI extraction and validation (validation resolves DOIs online through python-doi)."""
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, unquote

import doi as pydoi

from ._progress import bar

DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>{}|^`\\]+", re.I)
_cache = {}


def extract_dois(text):
    """Return the set of DOIs found in text (URL-encoding and trailing punctuation removed)."""
    text = text.replace("\\_", "_").replace("\\%", "%").replace("\\&", "&")
    found = set()
    for m in DOI_RE.finditer(unquote(pydoi.get_clean_doi(text))):
        d = m.group(0).rstrip(".,;:)]'\u201d\u2019")
        if d.count("(") < d.count(")"):
            d = d.rstrip(")")
        found.add(d)
    return found


def _validate_one(d):
    try:
        url = pydoi.validate_doi(quote(d, safe="/:()"))
        return ("valid", url) if url else ("invalid", "DOI resolves to no URL")
    except ValueError as e:
        return ("invalid", str(e))
    except Exception as e:  # network trouble: not evidence the DOI is bad
        return ("unknown", f"{type(e).__name__}: {e}")


def validate_all(dois):
    """Return {doi: (status, detail)} with status in valid/invalid/unknown. Results are cached per run."""
    todo = [d for d in dois if d not in _cache]
    if todo:
        socket.setdefaulttimeout(20)
        with ThreadPoolExecutor(max_workers=8) as pool:
            with bar(len(todo), "Validating DOIs") as pb:
                for d, res in zip(todo, pool.map(_validate_one, todo)):
                    _cache[d] = res
                    pb.update(1)
    return {d: _cache[d] for d in dois}


def findings(doi_locations, config, name, category, Finding, Level):
    """doi_locations: {doi: set(location)}. Returns findings for invalid / unverifiable DOIs plus a summary."""
    if not doi_locations:
        return []
    out = []
    if not config.get("validate_dois", True):
        return [Finding(Level.INFO, name, "-", f"{len(doi_locations)} DOI(s) found; online validation disabled", category)]
    results = validate_all(list(doi_locations))
    unknown = []
    for d, (status, detail) in sorted(results.items()):
        loc = sorted(doi_locations[d])[0]
        if status == "invalid":
            out.append(Finding(Level.ERROR, name, loc, f"Invalid DOI {d}: {detail}", category))
        elif status == "unknown":
            unknown.append(d)
    if unknown:
        out.append(Finding(Level.WARNING, name, "-", f"Could not validate {len(unknown)} DOI(s) (network problem?): {', '.join(unknown[:3])}{'...' if len(unknown) > 3 else ''}", category))
    ok = sum(1 for s, _ in results.values() if s == "valid")
    out.append(Finding(Level.INFO, name, "-", f"{ok} of {len(results)} DOI(s) validated", category))
    return out

