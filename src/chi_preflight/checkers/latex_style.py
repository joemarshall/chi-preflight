import re

from ..findings import Finding, Level
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-style"
CATEGORY = "style"
LEVEL = "quick"


def _parse(text):
    m = re.search(r"\\documentclass\s*(?:\[([^\]]*)\])?\s*\{([^}]+)\}", text)
    if not m:
        return None
    opts = {o.split("=")[0].strip() for o in (m.group(1) or "").split(",") if o.strip()}
    return m.group(2).strip(), opts


def check(folders, config):
    cfg = config["latex"]
    cls, required, forbidden = cfg["document_class"], cfg["required_options"], cfg["forbidden_options"]
    out = []
    mains = []
    for f in tex_files(folders):
        parsed = _parse(strip_comments(read(f)))
        if parsed:
            mains.append((f, *parsed))
    for f, got_cls, opts in mains:
        if cls and got_cls != cls:
            out.append(Finding(Level.ERROR, NAME, str(f), f"Document class is '{got_cls}', expected '{cls}'"))
            continue
        for o in required:
            if o not in opts:
                out.append(Finding(Level.ERROR, NAME, str(f), f"Required class option missing: {o}"))
        for o in forbidden:
            if o in opts:
                out.append(Finding(Level.ERROR, NAME, str(f), f"Class option not allowed: {o}"))
        out.append(Finding(Level.INFO, NAME, str(f), f"\\documentclass[{', '.join(sorted(opts))}]{{{got_cls}}}"))
    return out
