import argparse
import sys
from pathlib import Path

from print_color import print as cprint

from . import config as cfgmod
from .checkers import (docx_authors, latex_authors, pdf_authors, latex_style, docx_wordcount, docx_bibliography, latex_bib, docx_content, docx_metadata, docx_structure, latex_content,
                       latex_references, latex_structure, latex_wordcount, pdf_content, pdf_layout, pdf_metadata)
from .findings import Finding, Level

COLORS = {Level.ERROR: "red", Level.WARNING: "yellow", Level.INFO: "green"}

LATEX = [latex_authors, latex_structure, latex_style, latex_references, latex_bib, latex_content, latex_wordcount]
DOCX = [docx_authors, docx_metadata, docx_structure, docx_content, docx_bibliography, docx_wordcount]
PDF = [pdf_authors, pdf_metadata, pdf_layout, pdf_content]


def run(checkers, target, findings, config):
    for mod in checkers:
        try:
            new = mod.check(target, config)
            for f in new:
                f.category = mod.CATEGORY
            findings.extend(new)
        except Exception as e:  # a failing checker must not stop the others
            findings.append(Finding(Level.ERROR, mod.NAME, str(target), f"Checker crashed: {e!r}", mod.CATEGORY))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="chi-preflight", description="Preflight checks for submissions.")
    ap.add_argument("--latex", "-l", nargs="+", metavar="DIR", help="LaTeX source folder(s)")
    ap.add_argument("--docx", "-w", metavar="FILE", help="Word document")
    ap.add_argument("--pdf", "-p", metavar="FILE", help="PDF file")
    ap.add_argument("--config", "-c", default="anonymous", metavar="NAME|FILE",
                    help="built-in config (%s) or path to a YAML file (default: anonymous)"
                    % ", ".join(cfgmod.builtin_names()))
    args = ap.parse_args(argv)
    if not (args.latex or args.docx or args.pdf):
        ap.error("provide at least one of --latex, --docx, --pdf")

    try:
        config = cfgmod.load(args.config)
    except (FileNotFoundError, ValueError) as e:
        ap.error(str(e))

    findings = []
    if args.latex:
        missing = [d for d in args.latex if not Path(d).is_dir()]
        for d in missing:
            findings.append(Finding(Level.ERROR, "input", d, "Not a directory", "input"))
        folders = [d for d in args.latex if d not in missing]
        if folders:
            run(LATEX, folders, findings, config)
    for path, checkers in ((args.docx, DOCX), (args.pdf, PDF)):
        if not path:
            continue
        if not Path(path).is_file():
            findings.append(Finding(Level.ERROR, "input", path, "File not found", "input"))
        else:
            run(checkers, path, findings, config)

    findings.sort(key=lambda f: (-f.level, f.category))
    print("=== chi-preflight report ===")
    for f in findings:
        cprint(f, color=COLORS[f.level])
    counts = {l: sum(f.level == l for f in findings) for l in Level}
    print(f"\n{counts[Level.ERROR]} error(s), {counts[Level.WARNING]} warning(s), {counts[Level.INFO]} info")
    return 1 if counts[Level.ERROR] else 0


if __name__ == "__main__":
    sys.exit(main())




