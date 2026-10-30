from pathlib import Path

import yaml

BUILTIN = Path(__file__).parent / "configs"
DEFAULTS = {"anonymous": True, "max_words": None, "bibliography_heading": "Bibliography", "bibliography_style": None, "banned_text": {}, "validate_dois": True, "check_doi_titles": True, "check_reference_links": True, "max_abstract_words": None, "min_abstract_words": 10, "abstract_style": None, "latex": {"document_class": None, "required_options": [], "forbidden_options": []}}


def builtin_names():
    return sorted(p.stem for p in BUILTIN.glob("*.yaml"))


def load(spec):
    """spec is a built-in name (e.g. 'anonymous', 'camera-ready') or a path to a YAML file."""
    path = Path(spec)
    if not path.is_file():
        path = BUILTIN / (spec.replace("-", "_") + ".yaml")
    if not path.is_file():
        raise FileNotFoundError(f"Config not found: {spec} (built-in: {', '.join(builtin_names())})")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cfg = {**DEFAULTS, **data}
    cfg["latex"] = {**DEFAULTS["latex"], **(data.get("latex") or {})}
    return cfg

