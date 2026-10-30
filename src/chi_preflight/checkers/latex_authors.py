import re

from ..findings import Finding, Level
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-authors"


def _arg(text, start):
    """Return the brace-delimited argument beginning at text[start] == '{'."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    return text[start + 1:]


def _commands(text, name):
    for m in re.finditer(r"\\%s\*?(?:\[[^\]]*\])?\s*\{" % name, text):
        yield m.start(), _arg(text, m.end() - 1)


def check(folders, config):
    anon = config.get("anonymous", True)
    out = []
    for f in tex_files(folders):
        t = strip_comments(read(f))
        if r"\documentclass" not in t:
            continue
        authors = [(pos, a) for pos, a in _commands(t, "author") if a.strip()]
        orcids = [pos for pos, a in _commands(t, "orcid") if a.strip()]
        class_anon = bool(re.search(r"\\documentclass\s*\[[^\]]*\banonymous\b", t))
        if anon:
            # With acmart's 'anonymous' option the source still holds names but they are not typeset
            lvl = Level.WARNING if class_anon else Level.ERROR
            suffix = " (hidden in output by 'anonymous' option, but present in source)" if class_anon else ""
            for _, a in authors:
                out.append(Finding(lvl, NAME, str(f), f"Author information present: \\author{{{' '.join(a.split())[:60]}}}{suffix}"))
            for cmd in ("affiliation", "email", "orcid", "thanks"):
                for _, a in _commands(t, cmd):
                    if a.strip():
                        out.append(Finding(lvl, NAME, str(f), f"Identifying \\{cmd} present: {' '.join(a.split())[:60]}{suffix}"))
            if re.search(r"\\begin\{acks\}|\\section\*?\{Acknowledg", t):
                out.append(Finding(Level.WARNING, NAME, str(f), "Acknowledgements section present (may identify authors)"))
            m = re.search(r"pdfauthor\s*=\s*\{?([^,}]+)", t)
            if m:
                out.append(Finding(Level.ERROR, NAME, str(f), f"hyperref pdfauthor set: {m.group(1).strip()}"))
        else:
            if not authors:
                out.append(Finding(Level.ERROR, NAME, str(f), r"No \author information found"))
                continue
            bounds = [p for p, _ in authors] + [len(t)]
            for i, (pos, a) in enumerate(authors):
                if not any(pos < o < bounds[i + 1] for o in orcids):
                    out.append(Finding(Level.WARNING, NAME, str(f), f"Author has no \\orcid: {' '.join(a.split())[:60]}"))
            out.append(Finding(Level.INFO, NAME, str(f), f"{len(authors)} author(s) found"))
    return out
