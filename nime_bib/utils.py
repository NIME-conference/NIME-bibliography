from bibtexparser.bwriter import BibTexWriter
from pathlib import Path

# paths
BASE_PATH = Path(".")
PAPER_PROC = BASE_PATH / "paper_proceedings"
MUSIC_PROC = BASE_PATH / "music_proceedings"
INSTALL_PROC = BASE_PATH / "installation_proceedings"
ALT_PROC = BASE_PATH / "alt_proceedings"
RELEASE_PATH = BASE_PATH / "release"
BIB_EXT = ".bib"

def collated_path(proc_type, file_format):
    """Returns the path for storing the collated proceedings of a given type and file format.
    """

    RELEASE_PATH.mkdir(parents=True, exist_ok=True)
    if proc_type == "paper":
        return RELEASE_PATH / f"nime_papers.{file_format}"
    elif proc_type == "installation":
        return RELEASE_PATH / f"nime_installations.{file_format}"
    elif proc_type == "music":
        return RELEASE_PATH / f"nime_music.{file_format}"
    elif proc_type == "alt":
        return RELEASE_PATH / f"nime_alt.{file_format}"
    else:
        return None    

def path_for_proc(year, proc_type):
    """Returns the path for a proceeding for a given year and type.
    """
    if proc_type == "paper":
        return PAPER_PROC / f"nime{year}.bib"
    elif proc_type == "installation":
        return INSTALL_PROC / f"nime{year}_installations.bib"
    elif proc_type == "music":
        return MUSIC_PROC / f"nime{year}_music.bib"
    elif proc_type == "alt":
        return ALT_PROC / f"nime{year}_alt.bib"
    else:
        return None

def glob_for_proc(proc_type):
    """Returns the available proceedings files for a given type, sorted by
    filename (i.e. by year).

    Sorted deliberately: Path.glob returns filesystem order, which differs
    between macOS and the Linux CI runner and would make the collated output
    non-reproducible.
    """
    if proc_type == "paper":
        return sorted(PAPER_PROC.glob("nime*.bib"))
    elif proc_type == "installation":
        return sorted(INSTALL_PROC.glob("nime*_installations.bib"))
    elif proc_type == "music":
        return sorted(MUSIC_PROC.glob("nime*_music.bib"))
    elif proc_type == "alt":
        return sorted(ALT_PROC.glob("nime*_alt.bib"))
    else:
        return []


# field order for nime proc entries.
FIELD_ORDER = ("author",
               "title",
               "pages",
               "booktitle",
               "volume",
               "series",
               "editor",
               "year",
               "month",
               "date",
               "day",
               "publisher",
               "address",
               "isbn",
               "issn",
               "articleno",
               "track",
               "note",
               "doi",
               "url",
               "url2",
               "url3",
               "urlsuppl1",
               "urlsuppl2",
               "urlsuppl3",
               "pdf",
               "presentation-video", 
               "keywords",
               "abstract")


# bibtex entries indented by a single space
FIELD_INDENT = "  "

# Writer object to use for writing back nime proceedings in the correct format.
writer = BibTexWriter()
writer.indent = FIELD_INDENT
writer.display_order = FIELD_ORDER
writer.common_strings = False # would like it to write month 3-letter codes, but can't seem to avoid writing them at the start of each file weirdly.
writer.order_entries_by = ("articleno", "url", "ID")


# all proceedings types, in the order used for reporting
PROC_TYPES = ("paper", "music", "installation", "alt")

# fields that are published as UTF-8 and should not contain LaTeX escapes
PUBLISHED_TEXT_FIELDS = ("title", "author", "abstract", "keywords")

# fields every entry is expected to carry
REQUIRED_FIELDS = ("author", "title", "year", "booktitle")


def all_proc_files():
    """Yields (proc_type, path) for every available proceedings file."""
    for proc_type in PROC_TYPES:
        for path in sorted(glob_for_proc(proc_type)):
            yield proc_type, path
