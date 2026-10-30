# chi-preflight

Preflight checks for CHI-style (ACM) submissions. Runs a set of checkers over your LaTeX sources, Word document and/or PDF, collects every error, warning and info message, and prints them at the end.

## Install

Requires Python 3.9+. On non-windows systems, you need perl installed. On Windows it auto-downloads a perl interpreter on first run. 

# Usage:

clone the repository, install with pip

```
pip install -e .
```

This installs the `chi-preflight` command and the dependencies: `PyPDF2`, `python-docx`, `PyYAML`, `print-color` and `python-doi`.

## Usage

```
chi-preflight [--config NAME|FILE] [--latex DIR [DIR ...]] [--docx FILE.docx] [--pdf FILE.pdf]
                [--format text|csv] [--output FILE]
```

| Option | Description |
|---|---|
| `-l`, `--latex` | One or more LaTeX source folders (searched recursively for `.tex` / `.bib`) |
| `-w`, `--docx` | Word document |
| `-p`, `--pdf` | PDF file |
| `-c`, `--config` | Built-in config name (`anonymous`, `camera_ready`) or a path to a YAML file. Default: `anonymous` |
| `-f`, `--format` | Output format for the whole report: `text` (default) or `csv`. CSV mode prints only CSV to the terminal |
| `-o`, `--output` | Also write the report to this file, in the chosen format. Nothing is written to a file unless this is given |

At least one of `--latex`, `--docx`, `--pdf` is required. Examples:

```
chi-preflight -c anonymous --latex paper/ --docx paper.docx --pdf paper.pdf
chi-preflight -c camera_ready --latex paper/
chi-preflight -c my_config.yaml --pdf paper.pdf
```

Output lines look like `[ERROR] [category] checker: location: message`, coloured red (error), yellow (warning) and green (info), sorted by severity then category. A saved CSV report has the columns `level, category, checker, location, message` (UTF-8 with BOM so Excel opens it correctly). The exit code is `1` if there are any errors, otherwise `0`.

## Checks

| Category | LaTeX | Word | PDF |
|---|---|---|---|
| anonymity | `latex_authors` | `docx_authors` | `pdf_authors` |
| references | `latex_references`, `latex_bib`, `latex_dois` | `docx_bibliography`, `docx_dois` | `pdf_dois` |
| structure | `latex_structure`, `latex_ccs` | `docx_structure` | `pdf_layout` |
| style | `latex_style` | | |
| length | `latex_wordcount`, `latex_abstract` | `docx_wordcount`, `docx_abstract` | |
| metadata | | `docx_metadata` | `pdf_metadata` |
| content | `latex_content`, `latex_banned_text` | `docx_content`, `docx_banned_text` | `pdf_content`, `pdf_banned_text` |

Highlights:

- **Anonymity** (anonymous mode): errors on author names, affiliations, emails, ORCIDs, author metadata, comment/tracked-change authors, and PDF annotation authors. In camera-ready mode it instead requires authors to exist and warns about authors without an ORCID.
- **References**: undefined `\ref`/`\cite` keys, cited bib entries without a DOI (online-only entries are exempt), Word reference entries without a DOI, and every DOI found in the document is resolved online via doi.org.
- **Word counts** exclude the bibliography, appendices, tables, headers/footers and captions. LaTeX counts use `texcount` and stop at the first appendix or bibliography marker.
- **Abstract**: must exist, with a word count between the configured minimum and maximum.
- **CCS**: LaTeX must contain a non-empty `CCSXML` environment and a `\ccsdesc` command.
- **Banned text**: configurable phrases (e.g. template placeholders) reported as errors.

## Configuration

Built-in configs live in [`src/chi_preflight/configs/`](src/chi_preflight/configs): `anonymous.yaml` (anonymous submission) and `camera_ready.yaml`. Pass your own YAML with `-c`; omitted settings fall back to defaults.

| Setting | Meaning | Default |
|---|---|---|
| `anonymous` | `true`: no author information allowed. `false`: authors with ORCIDs expected | `true` |
| `max_words` | Maximum body word count (LaTeX and Word); `null` disables | none |
| `min_abstract_words` / `max_abstract_words` | Abstract word limits | `10` / none |
| `abstract_style` | Word paragraph style of the abstract; `null` finds an "Abstract" heading instead | none |
| `bibliography_heading` | Heading of the Word bibliography section | `Bibliography` (built-ins: `References`) |
| `bibliography_style` | Word paragraph style of reference entries (the bibliography ends at the first non-empty paragraph in another style); `null` accepts any | none (built-ins: `Bib_entry`) |
| `validate_dois` | Resolve every DOI online; set `false` when offline | `true` |
| `latex.document_class` | Required LaTeX class, e.g. `acmart` | none |
| `latex.required_options` / `latex.forbidden_options` | Class options, e.g. `[manuscript, review, anonymous]` | empty |
| `banned_text` | Map of `"phrase": "error message"`; matched case- and whitespace-insensitively | empty |

Example:

```yaml
anonymous: false
max_words: 12000
latex:
  document_class: acmart
  required_options: [sigconf]
  forbidden_options: [anonymous, review]
banned_text:
  "Insert your first CCS term here": "CCS concept placeholder still in file"
```

## texcount and Perl

LaTeX word counts use [texcount](https://app.uio.no/ifi/texcount/). On first use chi-preflight downloads it to a cache folder (`%LOCALAPPDATA%\chi-preflight` on Windows, `~/.cache/chi-preflight` elsewhere), unless `texcount` is already on your `PATH`. texcount needs Perl: if none is found, on Windows a portable Strawberry Perl (~300 MB) is downloaded once; on other systems a warning asks you to install Perl and the word count is skipped.

## Adding a checker

Each checker is a module in [`src/chi_preflight/checkers/`](src/chi_preflight/checkers) with `NAME`, `CATEGORY` and `check(target, config)` returning a list of `Finding` objects (`Level.ERROR`, `WARNING` or `INFO`). `target` is a list of folders for LaTeX checkers and a file path for Word/PDF checkers. Register the module in the `LATEX`, `DOCX` or `PDF` list in [`main.py`](src/chi_preflight/main.py). A checker that raises is reported as an error and doesn't stop the others.

