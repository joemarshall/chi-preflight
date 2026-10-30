import re

from ..findings import Finding, Level
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-ccs"
CATEGORY = "structure"
CCSDESC_RE = re.compile(r"\\ccsdesc(?:\[[^\]]*\])?\{([^}]*)\}")
CCSXML_RE = re.compile(r"\\begin\{CCSXML\}(.*?)\\end\{CCSXML\}", re.S)


def check(folders, config):
    out = []
    found = False
    for f in tex_files(folders):
        for m in CCSXML_RE.finditer(strip_comments(read(f))):
            found = True
            if not re.search(r"<\w[^>]*>", m.group(1)):
                out.append(Finding(Level.ERROR, NAME, str(f), "CCSXML environment has no XML content"))
            else:
                out.append(Finding(Level.INFO, NAME, str(f), "CCSXML environment present with XML content"))
    if not found:
        out.append(Finding(Level.ERROR, NAME, str(folders[0]), r"No \begin{CCSXML} environment found"))
    ccsdesc = [a for f in tex_files(folders)
               for a in CCSDESC_RE.findall(strip_comments(read(f))) if a.strip()]
    if not ccsdesc:
        out.append(Finding(Level.ERROR, NAME, str(folders[0]), r"No \ccsdesc command found"))
    else:
        out.append(Finding(Level.INFO, NAME, str(folders[0]), f"{len(ccsdesc)} \\ccsdesc command(s) found"))
    return out
