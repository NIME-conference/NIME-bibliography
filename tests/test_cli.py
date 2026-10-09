"""Tests for the nime_bib command line commands, run against small archives."""

import pytest
from click.testing import CliRunner

PAPER = """@inproceedings{nime2099_1,
  author = {Ada Lovelace},
  title = {A Paper},
  booktitle = {Proceedings of NIME},
  year = {2099},
  articleno = {1},
  numpages = {4},
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
    assert "* numpages: 1" in lines
    assert "  title: 1" in lines


def test_find_keys_is_gone(cli_module, archive):
    result = CliRunner().invoke(cli_module.cli, ["find-keys"])
    assert result.exit_code != 0
