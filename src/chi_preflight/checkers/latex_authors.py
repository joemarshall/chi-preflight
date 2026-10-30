import re

from ..findings import Finding, Level
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-authors"
CATEGORY = "anonymity"


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
    texts = {f: strip_comments(read(f)) for f in tex_files(folders)}
    # \input'd files (e.g. Authors.tex) have no \documentclass, so scan every file
    class_anon = any(re.search(r"\\documentclass\s*\[[^\]]*\banonymous\b", t) for t in texts.values())
    n_authors = 0
    for f, t in texts.items():
        authors = [(pos, a) for pos, a in _commands(t, "author") if a.strip()]
        orcids = [pos for pos, a in _commands(t, "orcid") if a.strip()]
        n_authors += len(authors)
        if anon:
            # With acmart's 'anonymous' option the source still holds names but they are not typeset
            lvl = Level.WARNING if class_anon else Level.ERROR
            suffix = " (hidden in output by 'anonymous' option, but present in source)" if class_anon else ""
            for _, a in authors:
                out.append(Finding(lvl, NAME, str(f), f"Author information present: \\author{{{' '.join(a.split())[:60]}}}{suffix}"))
            for cmd in ("affiliation", "email", "orcid", "thanks"):
                for _, a in _commands(t, cmd):
                    if a.strip():
                        # emails are always an error, even if the class hides them in the output
                        out.append(Finding(Level.ERROR if cmd == "email" else lvl, NAME, str(f), f"Identifying \\{cmd} present: {' '.join(a.split())[:60]}{suffix}"))
            if re.search(r"\\begin\{acks\}|\\section\*?\{Acknowledg", t):
                out.append(Finding(Level.WARNING, NAME, str(f), "Acknowledgements section present (may identify authors)"))
            email_args = {a.strip() for _, a in _commands(t, "email")}
            for e in sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", t))):
                if not any(e in a for a in email_args):
                    out.append(Finding(Level.ERROR, NAME, str(f), f"Email address in source: {e}"))
            m = re.search(r"pdfauthor\s*=\s*\{?([^,}]+)", t)
            if m:
                out.append(Finding(Level.ERROR, NAME, str(f), f"hyperref pdfauthor set: {m.group(1).strip()}"))
        else:
            bounds = [p for p, _ in authors] + [len(t)]
            for i, (pos, a) in enumerate(authors):
                if not any(pos < o < bounds[i + 1] for o in orcids):
                    out.append(Finding(Level.WARNING, NAME, str(f), f"Author has no \\orcid: {' '.join(a.split())[:60]}"))
    if not anon:
        if not n_authors:
            out.append(Finding(Level.ERROR, NAME, str(folders[0]), r"No \author information found"))
        else:
            out.append(Finding(Level.INFO, NAME, str(folders[0]), f"{n_authors} author(s) found"))
    return out
