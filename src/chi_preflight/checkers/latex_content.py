import re

from ..findings import Finding, Level
from ._latex_util import read, tex_files

NAME = "latex-content"


def check(folders, config):
    out = []
    for f in tex_files(folders):
        for n, line in enumerate(read(f).splitlines(), 1):
            if re.search(r"\b(TODO|FIXME|XXX)\b", line):
                out.append(Finding(Level.WARNING, NAME, f"{f}:{n}", "TODO/FIXME marker"))
            code = re.sub(r"(?<!\\)%.*", "", line)
            if "??" in code:
                out.append(Finding(Level.WARNING, NAME, f"{f}:{n}", "Literal '??' (unresolved reference?)"))
            if re.search(r"\\(?:vspace|hspace)\*?\{-", code) or r"\vspace" in code:
                out.append(Finding(Level.INFO, NAME, f"{f}:{n}", "Manual spacing adjustment (\\vspace/\\hspace)"))
    return out


