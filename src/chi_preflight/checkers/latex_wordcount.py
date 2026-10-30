import re
import subprocess
import tempfile
from pathlib import Path

from ..findings import Finding, Level
from ..texcount_support import get_texcount
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-wordcount"
CATEGORY = "length"

INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
# Counting stops at the first appendix or bibliography marker
STOP_RE = re.compile(
    r"\\appendix\b|\\begin\{appendices\}|\\bibliography\s*\{|\\printbibliography|\\begin\{thebibliography\}"
    r"|\\(?:chapter|section)\*?\s*\{\s*(?:appendix|appendices|references|bibliography)\b",
    re.I)


def _inline(path, base, seen=()):
    text = strip_comments(read(path))

    def repl(m):
        ref = m.group(1).strip()
        for cand in (base / ref, base / (ref + ".tex")):
            if cand.is_file() and cand.resolve() not in seen:
                return _inline(cand, base, seen + (cand.resolve(),))
        return ""
    return INPUT_RE.sub(repl, text)


def _body_text(main):
    text = _inline(main, main.parent, (main.resolve(),))
    m = STOP_RE.search(text)
    stopped = m is not None
    if m:
        text = text[:m.start()] + "\n\\end{document}\n"
    return text, stopped


def check(folders, config):
    cmd, problem = get_texcount()
    if not cmd:
        return [Finding(Level.WARNING, NAME, str(folders[0]), f"{problem}; word count skipped")]
    mains = [f for f in tex_files(folders) if r"\documentclass" in strip_comments(read(f))]
    if not mains:
        return [Finding(Level.WARNING, NAME, str(folders[0]), r"No main file (\documentclass) found; word count skipped")]
    out = []
    for main in mains:
        text, stopped = _body_text(main)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_file = Path(tmp) / "body.tex"
            tmp_file.write_text(text, encoding="utf-8")
            # -1 -sum prints just the total; includes were already inlined above
            proc = subprocess.run([*cmd, "-1", "-sum", str(tmp_file)],
                                  capture_output=True, text=True, errors="replace")
        m = re.search(r"\d+", proc.stdout)
        if proc.returncode != 0 or not m:
            out.append(Finding(Level.ERROR, NAME, str(main), f"texcount failed: {(proc.stderr or proc.stdout).strip()[:200]}", CATEGORY))
            continue
        n = int(m.group(0))
        note = "excluding appendices and bibliography" if stopped else "no appendix/bibliography marker found"
        out.append(Finding(Level.INFO, NAME, str(main), f"Word count (texcount): {n} ({note})"))
        limit = config.get("max_words")
        if limit and n > limit:
            out.append(Finding(Level.ERROR, NAME, str(main), f"Word count {n} exceeds maximum of {limit}"))
    return out
