"""Shared helpers for the LaTeX checkers."""
import re
from pathlib import Path


def tex_files(folders):
    for folder in folders:
        yield from sorted(Path(folder).rglob("*.tex"))


def read(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def strip_comments(text):
    return re.sub(r"(?<!\\)%.*", "", text)
