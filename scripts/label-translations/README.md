# label_translations.py

A script to stamp a standardized translation notice onto the first page of translated academic papers in PDF format.

![Example notice rendered on a paper](output-dir/101-translated-labeled.pdf)

---

## What it does

Adds an italic notice at the top of the first page of each translated PDF:

> *This article is a {LANGUAGE} translation of "{AUTHORS}. {YEAR}, {PAPER-TITLE}. Proceedings of the International Conference on New Interfaces for Musical Expression", independently translated by its authors. The paper was originally written, peer-reviewed, and accepted in English; the English version on nime.org should be regarded as the version of record.*

---

## Requirements

Python 3.10+ and two libraries:

```bash
pip install pypdf reportlab
```

**Font:** The notice is typeset in [Libertinus Serif Italic](https://github.com/alerque/libertinus/releases). Download `LibertinusSerif-Italic.ttf` and place it in the same folder as the script. If the font is not found, the script falls back to Helvetica Oblique.

---

## Folder structure

```
label_translations.py
LibertinusSerif-Italic.ttf        ← font file (optional but recommended)
translated-papers.tsv             ← metadata for each paper
input-dir/                        ← original translated PDFs
    {PAPER-ID}-translated.pdf
    ...
output-dir/                       ← labeled PDFs (created automatically)
    {PAPER-ID}-translated-labeled.pdf
    ...
```

---

## TSV format

`translated-papers.tsv` must be tab-separated with these columns:

| Column | Content | Example |
|--------|---------|---------|
| 0 | Paper ID | `{PAPER-ID}` |
| 1 | Paper title | `{PAPER-TITLE}` |
| 2 | Authors | `{LAST, FIRST; LAST2, FIRST2}` |
| 3 | Language code | `{LANGUAGE-CODE}` |

A header row is optional — it is skipped automatically if the first column is not a number.

**Author format:** semicolon-separated, either `Last, First` or `First Last` — the script detects which format is used. Affiliations in parentheses (e.g. `Smith, John (MIT)*`) are stripped automatically.

**Supported language codes:**

| Code | Language |
|------|----------|
| `ES` | Spanish |
| `PT-BR` | Portuguese |
| `FR` | French |
| `JA` | Japanese |
| `DE` | German |
| `IT` | Italian |
| `ZH` | Chinese |
| `AR` | Arabic |
| `KO` | Korean |
| `RU` | Russian |

---

## PDF naming convention

| | Pattern |
|---|---|
| Input | `{PAPER_ID}-translated.pdf` |
| Output | `{PAPER_ID}-translated-labeled.pdf` |

---

## Usage

**Run with defaults** (reads `translated-papers.tsv`, `input-dir/`, writes to `output-dir/`):

```bash
python3 label_translations.py
```

**Run with custom paths:**

```bash
python3 label_translations.py \
  --tsv my-papers.tsv \
  --input-dir ./translations \
  --output-dir ./labeled
```

**All options:**

```
--tsv FILE              TSV file with paper metadata (default: translated-papers.tsv)
--input-dir DIR         Folder with input PDFs (default: input-dir)
--output-dir DIR        Folder for output PDFs (default: output-dir)
--font FILE             Path to an italic TTF font
--year YEAR             Publication year (default: set in script)
--conference NAME       Full conference name (default: set in script)
--proceedings-url URL   URL of the English version of record (default: set in script)
--id-col N              TSV column index for paper ID (default: 0)
--title-col N           TSV column index for title (default: 1)
--authors-col N         TSV column index for authors (default: 2)
--language-col N        TSV column index for language code (default: 3)
```

---

## Adapting for another conference or year

Open `label_translations.py` and edit the three lines near the top of the file:

```python
PROCEEDINGS_YEAR = 2026
PROCEEDINGS_CONFERENCE = "Proceedings of the International Conference on New Interfaces for Musical Expression"
PROCEEDINGS_URL = "nime.org"
```

---

## Example TSV

```tsv
paper_id	title	authors	language
{PAPER-ID}	{PAPER-TITLE}	{LAST, FIRST; LAST2, FIRST2}	{LANGUAGE-CODE}
```

## Acknowledgements

Thanks to João Tragtenberg for developing the script to label translated version of nime papers.