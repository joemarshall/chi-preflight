import re
from pathlib import Path

from ..findings import Finding, Level
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-references"


def check(folders, config):
    out = []
    texts = {f: strip_comments(read(f)) for f in tex_files(folders)}
    alltext = "\n".join(texts.values())
    labels = set(re.findall(r"\\label\{([^}]+)\}", alltext))
    bib_keys = set()
    for folder in folders:
        for b in Path(folder).rglob("*.bib"):
            bib_keys |= set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", read(b)))
    has_bib = bool(bib_keys) or r"\begin{thebibliography}" in alltext
    bib_items = set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", alltext))
    for f, t in texts.items():
        for m in re.finditer(r"\\(?:ref|autoref|cref|Cref|eqref|pageref)\{([^}]+)\}", t):
            for key in m.group(1).split(","):
                if key.strip() not in labels:
                    out.append(Finding(Level.ERROR, NAME, str(f), f"Undefined reference: {key.strip()}"))
        for m in re.finditer(r"\\cite\w*(?:\[[^\]]*\])*\{([^}]+)\}", t):
            for key in m.group(1).split(","):
                key = key.strip()
                if has_bib and key not in bib_keys and key not in bib_items:
                    out.append(Finding(Level.ERROR, NAME, str(f), f"Citation key not found: {key}"))
    if not has_bib and r"\cite" in alltext:
        out.append(Finding(Level.WARNING, NAME, str(folders[0]), "Citations used but no .bib file or bibliography found"))
    labs = re.findall(r"\\label\{([^}]+)\}", alltext)
    for dup in {l for l in labs if labs.count(l) > 1}:
        out.append(Finding(Level.WARNING, NAME, str(folders[0]), f"Duplicate label: {dup}"))
    return out

