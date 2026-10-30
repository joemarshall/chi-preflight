import re
from pathlib import Path

from ..findings import Finding, Level
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-structure"
CATEGORY = "structure"


def check(folders, config):
    out = []
    files = list(tex_files(folders))
    if not files:
        return [Finding(Level.ERROR, NAME, ", ".join(map(str, folders)), "No .tex files found")]
    texts = {f: strip_comments(read(f)) for f in files}
    if not any(r"\documentclass" in t for t in texts.values()):
        out.append(Finding(Level.ERROR, NAME, str(folders[0]), r"No \documentclass found"))
    if not any(r"\begin{document}" in t for t in texts.values()):
        out.append(Finding(Level.ERROR, NAME, str(folders[0]), r"No \begin{document} found"))
    for f, t in texts.items():
        for m in re.finditer(r"\\(input|include|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}", t):
            kind, ref = m.groups()
            base = f.parent / ref
            exts = ["", ".tex", ".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg"]
            if not any(Path(str(base) + e).is_file() for e in exts):
                out.append(Finding(Level.ERROR, NAME, str(f), f"\\{kind} target not found: {ref}"))
        for env in set(re.findall(r"\\begin\{([^}]+)\}", t)):
            b, e = t.count("\\begin{%s}" % env), t.count("\\end{%s}" % env)
            if b != e:
                out.append(Finding(Level.ERROR, NAME, str(f), f"Unbalanced environment '{env}' ({b} begin, {e} end)"))
    out.append(Finding(Level.INFO, NAME, str(folders[0]), f"Scanned {len(files)} .tex file(s)"))
    return out

