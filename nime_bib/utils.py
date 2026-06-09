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
    """Returns the glob of available procs for a given type.
    """
    if proc_type == "paper":
        return PAPER_PROC.glob(f"nime*.bib")
    elif proc_type == "installation":
        return INSTALL_PROC.glob(f"nime*_installations.bib")
    elif proc_type == "music":
        return MUSIC_PROC.glob(f"nime*_music.bib")
    elif proc_type == "alt":
        return ALT_PROC.glob(f"nime*_alt.bib")
    else:
        return None


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
