"""Nested progress bar (stderr) shown under the main per-check bar."""
import sys

from tqdm import tqdm


def bar(total, desc):
    return tqdm(total=total, desc=desc, file=sys.stderr, position=1, leave=False, unit="item")
