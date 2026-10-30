import re
import subprocess
import tempfile
from pathlib import Path

from ..findings import Finding, Level
from ..texcount_support import get_texcount
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-abstract"
CATEGORY = "length"
ABSTRACT_RE = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.S)


def _count(text):
    cmd, _ = get_texcount()
    if cmd:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "abstract.tex"
            f.write_text("\\begin{document}\n" + text + "\n\\end{document}\n", encoding="utf-8")
            proc = subprocess.run([*cmd, "-1", "-sum", str(f)], capture_output=True, text=True, errors="replace")
        m = re.search(r"\d+", proc.stdout)
        if proc.returncode == 0 and m:
            return int(m.group(0))
    # fallback: strip commands and count remaining words
    plain = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", text)
    return len(re.findall(r"[A-Za-z0-9][\w'-]*", plain))


def check(folders, config):
    limit = config.get("max_abstract_words")
    minimum = config.get("min_abstract_words")
    if not limit and not minimum:
        return []
    out = []
    found = False
    for f in tex_files(folders):
        for m in ABSTRACT_RE.finditer(strip_comments(read(f))):
            found = True
            n = _count(m.group(1))
            out.append(Finding(Level.INFO, NAME, str(f), f"Abstract word count: {n} (minimum {minimum or 0}, maximum {limit or 'none'})"))
            if minimum and n < minimum:
                out.append(Finding(Level.ERROR, NAME, str(f), f"Abstract has only {n} words, fewer than minimum of {minimum}"))
            if limit and n > limit:
                out.append(Finding(Level.ERROR, NAME, str(f), f"Abstract has {n} words, exceeding maximum of {limit}"))
    if not found:
        out.append(Finding(Level.ERROR, NAME, str(folders[0]), r"No \begin{abstract} environment found"))
    return out
