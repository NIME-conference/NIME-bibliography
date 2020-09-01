from bibtexparser.bwriter import BibTexWriter

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
               "publisher",
               "address",
               "isbn",
               "issn",
               "articleno",
               "track",
               "doi",
               "url",
               "urlsuppl1",
               "urlsuppl2",
               "urlsuppl3",
               "presentation-video", 
               "keywords",
               "abstract")

# bibtex entries indented by a single space
FIELD_INDENT = "	"

# Writer object to use for writing back nime proceedings in the correct format.
writer = BibTexWriter()
writer.indent = FIELD_INDENT
writer.display_order = FIELD_ORDER
writer.common_strings = False # would like it to write month 3-letter codes, but can't seem to avoid writing them at the start of each file weirdly.
writer.order_entries_by = ("articleno", "url", "ID")
