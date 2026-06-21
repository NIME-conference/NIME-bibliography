#!/usr/bin/env python3
"""
label_translations.py — Add a translation notice to the first page of translated academic papers.

USAGE
-----
    # Default (uses translated-papers.tsv, input-dir/, output-dir/):
    python3 label_translations.py

    # With custom paths:
    python3 label_translations.py \\
        --tsv papers.tsv \\
        --input-dir ./translations \\
        --output-dir ./labeled \\
        --font /path/to/LibertinusSerif-Italic.ttf \\
        --year 2026 \\
        --conference "Proceedings of the International Conference on New Interfaces for Musical Expression" \\
        --proceedings-url nime.org

TSV FORMAT
----------
The TSV file must have one paper per row with these columns (no header row required,
but a header row is skipped automatically if the first column is not a number):

    col 0  — Paper ID        e.g.  459
    col 1  — Paper title     e.g.  Between Intimacy and Immensity: ...
    col 2  — Authors         e.g.  Last, First; Last2, First2; Last3, First3
                                   OR  First Last; First2 Last2  (auto-detected)
    col 3  — Language code   e.g.  ES, PT-BR, FR, JA, DE, IT, ZH

    Author names may include affiliations in parentheses (e.g. "Smith, John (MIT)*")
    — these are stripped automatically.

    Column indices can be overridden with --id-col, --title-col, --authors-col, --language-col.

PDF NAMING CONVENTION
---------------------
    Input files must be named:   {PAPER_ID}-translated.pdf
    Output files will be named:  {PAPER_ID}-translated-labeled.pdf

    If --output-dir is not set, labeled files are written next to the originals.

FONT
----
    The notice is rendered in italic Libertinus Serif or Sans (https://github.com/alerque/libertinus).
    The simplest setup: drop LibertinusSerif-Italic.ttf or LibertinusSans-Italic.ttf
    in the same folder as this script — it will be found automatically.
    If --font is not given, the script also checks common macOS and Linux system paths.
    Falls back to Helvetica Oblique if no Libertinus font is found.
"""

import argparse
import csv
import io
import re
import sys
from pathlib import Path

from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

# ══════════════════════════════════════════════════════════════════════════════
# CONFERENCE SETTINGS — edit here when reusing for a different year/conference
# ══════════════════════════════════════════════════════════════════════════════

PROCEEDINGS_YEAR = 2026
PROCEEDINGS_CONFERENCE = "Proceedings of the International Conference on New Interfaces for Musical Expression"
PROCEEDINGS_URL = "nime.org"

# ══════════════════════════════════════════════════════════════════════════════

# ── Language code → display name ──────────────────────────────────────────────

LANGUAGE_NAMES: dict[str, str] = {
    "ES": "Spanish",
    "PT-BR": "Portuguese",
    "FR": "French",
    "JA": "Japanese",
    "DE": "German",
    "IT": "Italian",
    "ZH": "Chinese",
    "AR": "Arabic",
    "KO": "Korean",
    "RU": "Russian",
}

# ── Font discovery ─────────────────────────────────────────────────────────────

_SCRIPT_DIR = Path(__file__).parent

FONT_SEARCH_PATHS = [
    # Script's own directory first — drop any Libertinus .ttf next to the script
    _SCRIPT_DIR / "LibertinusSerif-Italic.ttf",
    _SCRIPT_DIR / "LibertinusSans-Italic.ttf",
    # macOS user fonts
    Path.home() / "Library/Fonts/LibertinusSerif-Italic.ttf",
    Path.home() / "Library/Fonts/LibertinusSans-Italic.ttf",
    # macOS system fonts
    Path("/Library/Fonts/LibertinusSerif-Italic.ttf"),
    Path("/Library/Fonts/LibertinusSans-Italic.ttf"),
    # Linux
    Path("/usr/share/fonts/libertinus/LibertinusSerif-Italic.ttf"),
    Path("/usr/share/fonts/libertinus/LibertinusSans-Italic.ttf"),
    Path("/usr/share/fonts/truetype/libertinus/LibertinusSerif-Italic.ttf"),
    Path("/usr/share/fonts/truetype/libertinus/LibertinusSans-Italic.ttf"),
]

FONT_NAME = "NoticeFont"


def find_font(explicit: str | None) -> str | None:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            sys.exit(f"Error: font not found at {explicit}")
        return str(p)
    for p in FONT_SEARCH_PATHS:
        if p.exists():
            return str(p)
    return None  # caller falls back to built-in


def register_font(font_path: str | None) -> str:
    """Register the font and return the reportlab font name to use."""
    if font_path:
        pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
        return FONT_NAME
    return "Helvetica-Oblique"  # built-in fallback, no registration needed


# ── Author formatting ──────────────────────────────────────────────────────────

def _clean_author(name: str) -> str:
    """Strip affiliations in parentheses and trailing asterisks."""
    return re.sub(r"\s*\([^)]*\)\*?", "", name).strip()


def format_authors(authors_str: str) -> str:
    """
    Convert a semicolon-separated author list to a readable citation string.

    Accepts two formats:
      - "Last, First; Last2, First2"  →  reordered to "First Last, First2 Last2, ..."
      - "First Last; First2 Last2"    →  used as-is
    """
    parts = [_clean_author(a) for a in authors_str.split(";") if a.strip()]

    # Detect "Last, First" format: at least one entry contains a comma
    last_first = any("," in p for p in parts)

    formatted = []
    for part in parts:
        if last_first and "," in part:
            last, first = [s.strip() for s in part.split(",", 1)]
            formatted.append(f"{first} {last}")
        else:
            formatted.append(part)

    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}"
    return ", ".join(formatted[:-1]) + f", and {formatted[-1]}"


# ── Notice text ────────────────────────────────────────────────────────────────

def build_notice(
    authors: str,
    title: str,
    language_code: str,
    year: int,
    conference: str,
    proceedings_url: str,
) -> str:
    language = LANGUAGE_NAMES.get(language_code.upper(), language_code)
    authors_fmt = format_authors(authors)
    return (
        f'This article is a {language} translation of '
        f'"{authors_fmt}. {year}, {title}. {conference}", '
        f'independently translated by its authors. '
        f'The paper was originally written, peer-reviewed, and accepted in English; '
        f'the English version on {proceedings_url} should be regarded as the version of record.'
    )


# ── PDF overlay ────────────────────────────────────────────────────────────────

def create_overlay(
    page_width: float, page_height: float, text: str, font_name: str
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    font_size = 8.5
    margin = 30
    line_height = font_size * 1.35
    text_width = page_width - 2 * margin

    c.setFont(font_name, font_size)
    lines = simpleSplit(text, font_name, font_size, text_width)

    y = (page_height - 12) - font_size
    for line in lines:
        c.drawString(margin, y, line)
        y -= line_height

    c.save()
    buf.seek(0)
    return buf.read()


def stamp_pdf(input_path: Path, output_path: Path, notice: str, font_name: str) -> None:
    reader = PdfReader(str(input_path))
    writer = PdfWriter()

    first = reader.pages[0]
    w = float(first.mediabox.width)
    h = float(first.mediabox.height)

    overlay_bytes = create_overlay(w, h, notice, font_name)
    overlay_page = PdfReader(io.BytesIO(overlay_bytes)).pages[0]
    first.merge_page(overlay_page)

    writer.add_page(first)
    for page in reader.pages[1:]:
        writer.add_page(page)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


# ── TSV loading ────────────────────────────────────────────────────────────────

def load_tsv(
    tsv_path: Path, id_col: int, title_col: int, authors_col: int, lang_col: int
) -> dict[str, dict]:
    papers: dict[str, dict] = {}
    max_col = max(id_col, title_col, authors_col, lang_col)

    with open(tsv_path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) <= max_col:
                continue
            if not row[id_col].strip().isdigit():
                continue  # skip header or malformed rows
            paper_id = row[id_col].strip()
            papers[paper_id] = {
                "title": row[title_col].strip(),
                "authors": row[authors_col].strip(),
                "language": row[lang_col].strip(),
            }
    return papers


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stamp a translation notice onto translated academic PDFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--tsv", default="translated-papers.tsv", metavar="FILE",
                   help="TSV file with paper metadata (default: translated-papers.tsv)")
    p.add_argument("--input-dir", default="input-dir", metavar="DIR",
                   help="Folder containing {ID}-translated.pdf files (default: input-dir)")
    p.add_argument("--output-dir", default="output-dir", metavar="DIR",
                   help="Where to write {ID}-translated-labeled.pdf (default: output-dir)")
    p.add_argument("--font", metavar="FILE",
                   help="Path to an italic TTF font (default: auto-detect Libertinus Serif Italic)")
    p.add_argument("--year", type=int, default=PROCEEDINGS_YEAR, metavar="YEAR",
                   help=f"Publication year (default: {PROCEEDINGS_YEAR})")
    p.add_argument("--conference", default=PROCEEDINGS_CONFERENCE, metavar="NAME",
                   help="Full conference name")
    p.add_argument("--proceedings-url", default=PROCEEDINGS_URL, metavar="URL",
                   help=f"URL where the English version of record is hosted (default: {PROCEEDINGS_URL})")
    p.add_argument("--id-col", type=int, default=0, metavar="N",
                   help="TSV column index for paper ID (default: 0)")
    p.add_argument("--title-col", type=int, default=1, metavar="N",
                   help="TSV column index for paper title (default: 1)")
    p.add_argument("--authors-col", type=int, default=2, metavar="N",
                   help="TSV column index for authors (default: 2)")
    p.add_argument("--language-col", type=int, default=3, metavar="N",
                   help="TSV column index for language code (default: 3)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    tsv_path = Path(args.tsv)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir

    if not tsv_path.exists():
        sys.exit(f"Error: TSV file not found: {tsv_path}")
    if not input_dir.is_dir():
        sys.exit(f"Error: input directory not found: {input_dir}")

    font_path = find_font(args.font)
    font_name = register_font(font_path)
    if font_path:
        print(f"Font: {font_path}")
    else:
        print("Font: Libertinus Serif Italic not found — falling back to Helvetica Oblique")

    papers = load_tsv(tsv_path, args.id_col, args.title_col, args.authors_col, args.language_col)
    if not papers:
        sys.exit("Error: no valid rows found in TSV.")
    print(f"Loaded {len(papers)} papers from {tsv_path.name}\n")

    pdfs = sorted(input_dir.glob("*-translated.pdf"))
    if not pdfs:
        sys.exit(f"No files matching '*-translated.pdf' found in {input_dir}")

    ok = skipped = 0
    for pdf_path in pdfs:
        paper_id = pdf_path.stem.replace("-translated", "")
        if paper_id not in papers:
            print(f"  SKIP  {pdf_path.name}  (ID '{paper_id}' not in TSV)")
            skipped += 1
            continue

        info = papers[paper_id]
        notice = build_notice(
            info["authors"], info["title"], info["language"],
            args.year, args.conference, args.proceedings_url,
        )

        out_name = pdf_path.stem + "-labeled.pdf"
        output_path = output_dir / out_name

        stamp_pdf(pdf_path, output_path, notice, font_name)
        print(f"  OK    {pdf_path.name}  →  {output_path.name}")
        ok += 1

    print(f"\nDone: {ok} labeled, {skipped} skipped.")


if __name__ == "__main__":
    main()
