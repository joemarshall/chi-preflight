"""Online checks for references without a DOI: URL liveness and exact-title web search."""
import html
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

import requests

from ..findings import Finding, Level

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
           "Accept-Language": "en"}
BLOCKED = {401, 403, 429, 451, 999}
_url_cache, _search_cache = {}, {}


def check_url(url):
    """Return (status, detail): ok / broken / unknown."""
    if url in _url_cache:
        return _url_cache[url]
    res = ("unknown", "no response")
    try:
        r = requests.head(url, headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code >= 400:  # many servers reject HEAD
            r = requests.get(url, headers=HEADERS, timeout=20, stream=True)
            r.close()
        if r.status_code < 400:
            res = ("ok", f"HTTP {r.status_code}")
        elif r.status_code in BLOCKED:
            res = ("unknown", f"HTTP {r.status_code} (site blocks automated checks)")
        else:
            res = ("broken", f"HTTP {r.status_code}")
    except requests.exceptions.Timeout:
        res = ("unknown", "timed out")
    except requests.exceptions.SSLError as e:
        res = ("broken", f"SSL error: {e.__class__.__name__}")
    except requests.exceptions.ConnectionError as e:
        res = ("broken", f"connection failed: {str(e)[:100]}")
    except requests.exceptions.RequestException as e:
        res = ("broken", f"{e.__class__.__name__}: {str(e)[:100]}")
    _url_cache[url] = res
    return res


def check_urls(urls):
    urls = list(urls)
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(urls, pool.map(check_url, urls)))


def _norm(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"[\W_]+", " ", text.lower()).strip()


def _results_text(engine, page):
    """Return the text of the organic results, or None if the page has no usable result list."""
    if engine == "bing":
        blocks = re.findall(r'<li class="b_algo".*?</li>', page, re.S)
        if blocks:
            return " ".join(blocks)
        return "" if 'class="b_no"' in page else None
    # google serves a JavaScript-only page to scripts; results are only usable when <h3> titles exist
    page = re.sub(r"<title>.*?</title>|value=\"[^\"]*\"", " ", page, flags=re.S)
    return page if "<h3" in page else None


def _search_engine(engine, url, title):
    r = requests.get(url, headers=HEADERS, timeout=20)
    low = r.text.lower()
    if r.status_code != 200 or "/sorry/" in r.url or "consent." in r.url or "unusual traffic" in low:
        return "unknown"
    text = _results_text(engine, r.text)
    if text is None:
        return "unknown"
    return "found" if _norm(title) in _norm(text) else "notfound"


def search_title(title):
    """Search the web for the exact title (Google, then Bing). Returns found / notfound / unknown."""
    if title in _search_cache:
        return _search_cache[title]
    q = quote_plus(f'"{title}"')
    res = "unknown"
    for engine, url in (("google", f"https://www.google.com/search?q={q}&hl=en&num=10"),
                        ("bing", f"https://www.bing.com/search?q={q}&setlang=en")):
        try:
            res = _search_engine(engine, url, title)
        except requests.exceptions.RequestException:
            res = "unknown"
        if res != "unknown":
            break
    time.sleep(1.5)  # be polite to the search engines
    _search_cache[title] = res
    return res


def findings(refs, config, name, category):
    """refs: list of dicts {label, location, url, title}. All are references without a DOI."""
    if not refs:
        return []
    if not config.get("check_reference_links", True):
        return [Finding(Level.INFO, name, "-", f"{len(refs)} reference(s) without a DOI; online link/title checks disabled", category)]
    out = []
    urls = check_urls({r["url"] for r in refs if r["url"]})
    blocked = 0
    n_url = n_search = 0
    for r in refs:
        if r["url"]:
            n_url += 1
            status, detail = urls[r["url"]]
            if status == "broken":
                out.append(Finding(Level.ERROR, name, r["location"], f"Broken URL for {r['label']}: {r['url']} ({detail})", category))
            elif status == "unknown":
                out.append(Finding(Level.WARNING, name, r["location"], f"Could not verify URL for {r['label']}: {r['url']} ({detail})", category))
        elif not r["title"]:
            out.append(Finding(Level.WARNING, name, r["location"], f"No DOI or URL, and no title could be extracted to search for: {r['label']}", category))
        else:
            n_search += 1
            res = search_title(r["title"])
            if res == "notfound":
                out.append(Finding(Level.WARNING, name, r["location"], f'No DOI or URL, and exact title not found on the web: "{r["title"]}" ({r["label"]})', category))
            elif res == "unknown":
                blocked += 1
    if blocked:
        out.append(Finding(Level.WARNING, name, "-", f"Web search was blocked or unavailable; {blocked} title(s) could not be checked", category))
    out.append(Finding(Level.INFO, name, "-", f"Checked {n_url} URL(s) and searched for {n_search} title(s) for references without a DOI", category))
    return out
