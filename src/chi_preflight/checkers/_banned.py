import re


def normalise(text):
    return re.sub(r"\s+", " ", text).lower()


def find_banned(text, banned):
    """Yield (phrase, message) for each banned phrase present in text (case/whitespace-insensitive)."""
    norm = normalise(text)
    for phrase, message in (banned or {}).items():
        if normalise(str(phrase)) in norm:
            yield phrase, message
