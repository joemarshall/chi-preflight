import re
import shutil
import subprocess

from ..findings import Finding, Level
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-wordcount"


def check(folders, config):
    exe = shutil.which("texcount")
    if not exe:
        return [Finding(Level.WARNING, NAME, str(folders[0]), "texcount not found on PATH; word count skipped")]
    mains = [f for f in tex_files(folders) if r"\documentclass" in strip_comments(read(f))]
    if not mains:
        return [Finding(Level.WARNING, NAME, str(folders[0]), r"No main file (\documentclass) found; word count skipped")]
    out = []
    for main in mains:
        # -merge/-inc follow \input and \include; -1 -sum prints just the total
        proc = subprocess.run([exe, "-merge", "-inc", "-1", "-sum", main.name],
                              cwd=main.parent, capture_output=True, text=True, errors="replace")
        m = re.search(r"\d+", proc.stdout)
        if proc.returncode != 0 or not m:
            out.append(Finding(Level.ERROR, NAME, str(main), f"texcount failed: {(proc.stderr or proc.stdout).strip()[:200]}"))
        else:
            n = int(m.group(0))
            out.append(Finding(Level.INFO, NAME, str(main), f"Word count (texcount): {n}"))
            limit = config.get("max_words")
            if limit and n > limit:
                out.append(Finding(Level.ERROR, NAME, str(main), f"Word count {n} exceeds maximum of {limit}"))
    return out


