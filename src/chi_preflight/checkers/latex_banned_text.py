from ..findings import Finding, Level
from ._banned import find_banned, normalise
from ._latex_util import read, strip_comments, tex_files

NAME = "latex-banned-text"
CATEGORY = "content"


def check(folders, config):
    banned = config.get("banned_text")
    out = []
    for f in tex_files(folders):
        text = strip_comments(read(f))
        for phrase, message in find_banned(text, banned):
            needle = normalise(str(phrase))
            line = next((n for n, l in enumerate(text.splitlines(), 1) if needle in normalise(l)), None)
            loc = f"{f}:{line}" if line else str(f)
            out.append(Finding(Level.ERROR, NAME, loc, f"{message} (found: '{phrase}')"))
    return out
