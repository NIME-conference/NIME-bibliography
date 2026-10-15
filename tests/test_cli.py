"""Tests for the nime_bib command line commands, run against small archives."""

import json
import re
import sys

import pytest
from click.testing import CliRunner

PAPER = """@inproceedings{nime2099_1,
  author = {Ada Lovelace},
  title = {A Paper},
  booktitle = {Proceedings of NIME},
  year = {2099},
  articleno = {1},
  numpages = {4},
  frobnicate = {yes},
  url = {https://nime.org/proceedings/2099/nime2099_1.pdf}
}
"""

MUSIC = """@inproceedings{nime2099_music_Babbage,
  author = {Charles Babbage},
  title = {A Piece},
  booktitle = {Music Proceedings of NIME},
  year = {2099},
  url = {https://nime.org/proceedings/2099/nime2099_music_Babbage.pdf}
}
"""


def run(cli_module, *args):
    result = CliRunner().invoke(cli_module.cli, list(args))
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    return result


# collate (#103)

@pytest.mark.parametrize("fmt", ["bib", "csv", "yaml", "json"])
def test_collate_empty_directory(cli_module, archive, fmt):
    result = run(cli_module, "collate", "--type", "alt", "--format", fmt)
    assert "Saved 0 entries" in result.output


def test_collate_bib_collects_entries(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", PAPER)
    result = run(cli_module, "collate", "--type", "paper", "--format", "bib")
    assert "Saved 1 entries" in result.output
    with open("release/nime_papers.bib", encoding="utf-8") as f:
        assert "nime2099_1" in f.read()


# list-fields (#110)

def test_list_fields_lists_field_names_not_keys(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", PAPER)
    archive("music_proceedings/nime2099_music.bib", MUSIC)
    lines = run(cli_module, "list-fields").output.splitlines()

    assert "  author: 2" in lines
    assert "  articleno: 1" in lines
    # bibtexparser's internal names and the entry keys are not fields
    assert not any("ENTRYTYPE" in l or " ID:" in l or "nime2099" in l for l in lines)


def test_list_fields_marks_fields_missing_from_field_order(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", PAPER)
    lines = run(cli_module, "list-fields").output.splitlines()
    assert "* frobnicate: 1" in lines
    assert "  numpages: 1" in lines
    assert "  title: 1" in lines


def test_find_keys_is_gone(cli_module, archive):
    result = CliRunner().invoke(cli_module.cli, ["find-keys"])
    assert result.exit_code != 0


# collate converts every published text field, and builds the embedded
# bibtex field after conversion (#101, #108)

ACCENTED = r"""@inproceedings{nime2099_2,
  author = {Jacques R\'{e}mus},
  title = {Cam\'{e}ra},
  booktitle = {Proceedings of NIME},
  year = {2099},
  articleno = {2},
  keywords = {jacques r\'{e}mus,machines},
  url = {https://nime.org/proceedings/2099/nime2099_2.pdf}
}
"""


def test_collate_converts_keywords(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", ACCENTED)
    run(cli_module, "collate", "--type", "paper", "--format", "json")
    with open("release/nime_papers.json", encoding="utf-8") as f:
        text = json.load(f)
    assert text["keywords"]["0"] == "jacques rémus,machines"


def test_collate_bibtex_field_matches_converted_fields(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", ACCENTED)
    run(cli_module, "collate", "--type", "paper", "--format", "json")
    with open("release/nime_papers.json", encoding="utf-8") as f:
        bibtex = json.load(f)["bibtex"]["0"]
    assert "\\" not in bibtex
    assert "author = {Jacques Rémus}" in bibtex
    # written with utils.writer: canonical field order and indent
    assert bibtex.index("author") < bibtex.index("title") < bibtex.index("url")
    assert "\n  title = " in bibtex


# validate rejects stray 'and' in author lists (#91)

@pytest.mark.parametrize("author", [
    "Ada Lovelace and and Charles Babbage",
    "Ada Lovelace and, Charles Babbage",
    "and Ada Lovelace",
    "Ada Lovelace and",
    "and",
])
def test_validate_rejects_stray_and(cli_module, archive, author):
    archive("paper_proceedings/nime2099.bib",
            PAPER.replace("Ada Lovelace", author))
    result = CliRunner().invoke(cli_module.cli, ["validate"])
    assert result.exit_code != 0
    assert "stray 'and'" in result.output


@pytest.mark.parametrize("author", [
    "Ada Lovelace and Charles Babbage",
    "Holland, Quinn and Rolland, Jean-Baptiste",
    "Sandra Anderson",
    "Andrew Rand",
    "Ada Lovelace and Andrew Anderson",
])
def test_validate_accepts_well_formed_authors(cli_module, archive, author):
    archive("paper_proceedings/nime2099.bib",
            PAPER.replace("Ada Lovelace", author))
    result = CliRunner().invoke(cli_module.cli, ["validate"])
    assert "stray 'and'" not in result.output


# paths are resolved from the repository, not the working directory (#112)

def test_paths_do_not_depend_on_working_directory(cli_module, tmp_path,
                                                  monkeypatch):
    utils = sys.modules["utils"]
    monkeypatch.chdir(tmp_path)
    assert utils.PAPER_PROC.is_dir()
    assert (utils.PAPER_PROC / "nime2001.bib").is_file()


# every field in the data has a place in FIELD_ORDER (#105)

def test_field_order_covers_numpages_translations_copyright(cli_module):
    utils = sys.modules["utils"]
    for field in ("numpages", "translations", "copyright"):
        assert field in utils.FIELD_ORDER


def test_readme_template_matches_field_order(cli_module):
    utils = sys.modules["utils"]
    readme = (utils.BASE_PATH / "README.md").read_text(encoding="utf-8")
    template = readme.split("@inproceedings{article_id,", 1)[1].split("\n}", 1)[0]
    fields = re.findall(r"^\s+([\w-]+) = ", template, flags=re.M)
    assert tuple(fields) == utils.FIELD_ORDER


# add-dois checks the CSV and does not clobber existing DOIs (#104)

def write_csv(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def doi_of(path, key):
    with open(path, encoding="utf-8") as f:
        entry = f.read().split(f"{key},", 1)[1].split("\n}", 1)[0]
    m = re.search(r"doi = \{([^}]*)\}", entry)
    return m.group(1) if m else None


def test_add_dois_adds_doi(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", PAPER)
    write_csv("dois.csv", "key,doi\nnime2099_1.pdf,10.5281/zenodo.1\n")
    run(cli_module, "add-dois", "2099", "dois.csv", "--type", "paper")
    assert doi_of("paper_proceedings/nime2099.bib", "nime2099_1") == "10.5281/zenodo.1"


def test_add_dois_rejects_csv_without_doi_column(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", PAPER)
    write_csv("bad.csv", "key\nnime2099_1.pdf\n")
    result = CliRunner().invoke(
        cli_module.cli, ["add-dois", "2099", "bad.csv", "--type", "paper"])
    assert result.exit_code != 0
    assert "no doi column" in result.output
    assert "Traceback" not in result.output
    assert doi_of("paper_proceedings/nime2099.bib", "nime2099_1") is None


def test_add_dois_rejects_duplicate_keys(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", PAPER)
    write_csv("dup.csv", "key,doi\nnime2099_1.pdf,10.5281/zenodo.1\n"
                         "nime2099_1.pdf,10.5281/zenodo.2\n")
    result = CliRunner().invoke(
        cli_module.cli, ["add-dois", "2099", "dup.csv", "--type", "paper"])
    assert result.exit_code != 0
    assert "more than once" in result.output
    assert "nime2099_1 (10.5281/zenodo.1, 10.5281/zenodo.2)" in result.output
    assert doi_of("paper_proceedings/nime2099.bib", "nime2099_1") is None


WITH_DOI = PAPER.replace("  articleno", "  doi = {10.5281/zenodo.1},\n  articleno")


def test_add_dois_keeps_existing_doi_by_default(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", WITH_DOI)
    write_csv("dois.csv", "key,doi\nnime2099_1.pdf,10.5281/zenodo.2\n")
    result = run(cli_module, "add-dois", "2099", "dois.csv", "--type", "paper")
    assert "Kept the existing DOI" in result.output
    assert "1 entries kept their existing DOI: nime2099_1" in result.output
    assert doi_of("paper_proceedings/nime2099.bib", "nime2099_1") == "10.5281/zenodo.1"


def test_add_dois_overwrite_flag_replaces_doi(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", WITH_DOI)
    write_csv("dois.csv", "key,doi\nnime2099_1.pdf,10.5281/zenodo.2\n")
    result = run(cli_module, "add-dois", "2099", "dois.csv", "--type", "paper",
                 "--overwrite")
    assert "Kept the existing DOI" not in result.output
    assert doi_of("paper_proceedings/nime2099.bib", "nime2099_1") == "10.5281/zenodo.2"


def test_add_dois_same_doi_is_not_a_conflict(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", WITH_DOI)
    write_csv("dois.csv", "key,doi\nnime2099_1.pdf,10.5281/zenodo.1\n")
    result = run(cli_module, "add-dois", "2099", "dois.csv", "--type", "paper")
    assert "Kept the existing DOI" not in result.output


def test_add_dois_translated_checks_header_too(cli_module, archive):
    archive("paper_proceedings/nime2099.bib", PAPER)
    write_csv("bad.csv", "name,doi,title\nnime2099_1_Spanish.pdf,10.1/x,Un Papel\n")
    result = CliRunner().invoke(
        cli_module.cli,
        ["add-dois", "2099", "bad.csv", "--type", "paper", "--translated"])
    assert result.exit_code != 0
    assert "no key column" in result.output
