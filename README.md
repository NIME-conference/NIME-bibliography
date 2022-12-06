NIME-bibliography
=================

This is the bibliography files (in BibTeX format) of all publications from the annual [International Conference on New Interfaces for Musical Expression](http://www.nime.org) (NIME). These files are the source for the [NIME proceedings database](http://www.nime.org/archives/). 

The abstracts and keywords have been scraped from the each of the original PDF file using [this script](https://github.com/olovholm/NIME). We have been doing some automatic and manual cleaning up after running the script, but there are still linguistic (and other) errors in the database. Please help us clean it up!

The idea is that keeping the bibliography in an open and accessible format, it can be usable for the community, and it will also be easier to correct errors. 

Combined Files
--------

Combined files are automatically created after each commit by a GitHub Action and published to Github Pages.

The files can be found at [this repository's website](http://nime-conference.github.io/NIME-bibliography/), or the following URLs:

- [Combined Papers BibTeX](http://nime-conference.github.io/NIME-bibliography/nime_papers.bib)
- [Combined Music BibTeX](http://nime-conference.github.io/NIME-bibliography/nime_music.bib)
- [Combined Installations BibTeX](http://nime-conference.github.io/NIME-bibliography/nime_installations.bib)

Build 
--------

The `Makefile` creates combined files from the individual yearly BibTeX files for all proceedings types and places them in a directory called `release`. Outputs are created in `.bib`, `.csv` and `.yaml` format. 

The built proceedings are automatically deployed at <http://nime-conference.github.io/NIME-bibliography/>, separately to the main NIME website.

Publish on nime.org
----------

To update the bibliography on the [nime.org server](https://www.nime.org/archives/), it is necessary to run this script  

    sh get_publications.sh

in the [NIME Jekyll](https://github.com/NIME-conference/nime-website) repository.

`nime_bib` tool
--------

This repository contains a python tool called `nime_bib` to help systematically manage the proceedinggs, including tasks such as collating and harmonising files in different formats.

[Poetry](https://python-poetry.org) is used for dependency management. To use `nime_bib`, first [install Poetry](https://python-poetry.org), then run `poetry install` in the repository directory. You can then run `nime_bib` with the following command `poetry run python nime_bib`. The help file for `nime_bib` has the following output:

```
Usage: python -m nime_bib [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  collate    Collates all NIME proceedings of a certain type and saves to...
  find-keys  Finds all BibTeX keys used in all available proceedings files.
  harmonise  Loads a NIME proceedings BibTeX file for a given YEAR and...
```



Format
--------

The canonical format for a NIME proceedings bibtex entry is:

```
@inproceedings{article_id,
  author = {},
  title = {},
  pages = {},
  booktitle = {Proceedings of the International Conference on New Interfaces for Musical Expression},
  editor = {}
  year = {},
  month = {}
  date = {},
  address = {},
  isbn = {},
  issn = {},
  articleno = {},
  track = {},
  doi = {},
  url = {http://www.nime.org/proceedings/year/article_id.pdf},
  urlsuppl1 = {},
  urlsuppl2 = {},
  urlsuppl3 = {},
  pdf = {},
  presentation-video = {},
  keywords = {},
  abstract = {}
}
```

(more fields are under discussion in [issues](https://github.com/NIME-conference/NIME-bibliography/issues/13))

Articles should be ordered by page/article number within each proceedings file.

The script `scripts/harmonise_bibtex_file.py` can be used to ensure that proceedings files are in the above format.

Special characters in the `.bib` file should be written in LaTeX code.

Editing / Updates
--------

We welcome help from the community to edit and update errors in the proceedings. This is a volunteer effort!

Small edits can be done with a text editor and submitted as a [pull request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request).

Commits should **only affect** files and lines where an actual change is occurring (i.e., don't change the formatting of a file arbitrarily), this allows us to revert changes if anything goes wrong.

Larger projects (e.g., updating the URL or DOI fields for a whole year of the conference) should be done exclusively with scripts, Python scripts and notebooks for loading, editing, and saving bibtex files in our standardised format are provided under `/scripts`. In particular, `scripts/utils.py` has the canonical versions of the bibtex fields, ordering and sorting used in the proceedings.

We **do not suggest** using bibtex managers such as BibDesk/JabRef for small edits (although these are useful for browsing the proceedings) as these programs have a habit of changing the formatting and order of every single entry in a file.

Contact
-------

If you have questions about the bibliograpy, please get in touch with [Alexander Refsum Jensenius](http://people.uio.no/alexanje).
