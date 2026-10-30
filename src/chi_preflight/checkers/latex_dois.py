from ..findings import Finding, Level
from . import _doi
from ._latex_util import read, strip_comments
from pathlib import Path

NAME = "latex-dois"
CATEGORY = "references"


def check(folders, config):
    locs = {}
    for folder in folders:
        for f in sorted(list(Path(folder).rglob("*.tex")) + list(Path(folder).rglob("*.bib"))):
            text = read(f)
            if f.suffix == ".tex":
                text = strip_comments(text)
            for d in _doi.extract_dois(text):
                locs.setdefault(d, set()).add(str(f))
    return _doi.findings(locs, config, NAME, CATEGORY, Finding, Level)
