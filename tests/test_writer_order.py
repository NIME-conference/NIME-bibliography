"""Tests for entry ordering in the default bibtex writer (nime_bib.utils.writer)."""

import re

import bibtexparser
import pytest
from bibtexparser.bibdatabase import BibDatabase

from nime_bib import utils


def entry(ID, **fields):
    return {"ENTRYTYPE": "inproceedings", "ID": ID, **fields}


def written_ids(entries, order=("articleno", "url", "ID")):
    db = BibDatabase()
    db.entries = entries
    saved = utils.writer.order_entries_by
    utils.writer.order_entries_by = order
    try:
        out = utils.writer.write(db)
    finally:
        utils.writer.order_entries_by = saved
    return re.findall(r"@inproceedings\{([^,\s]+)", out)


def test_default_order_is_articleno_url_id():
    assert utils.writer.order_entries_by == ("articleno", "url", "ID")


def test_articleno_sorts_numerically():
    entries = [entry(f"p{n}", articleno=str(n)) for n in (100, 11, 2, 10, 1)]
    assert written_ids(entries) == ["p1", "p2", "p10", "p11", "p100"]


def test_articleno_whitespace_is_ignored():
    entries = [entry("ten", articleno="10"), entry("three", articleno=" 3 ")]
    assert written_ids(entries) == ["three", "ten"]


def test_unnumbered_entries_sort_last_by_url_then_id():
    entries = [
        entry("junk_b", articleno="abc", url="b"),
        entry("empty_a", articleno="", url="a"),
        entry("missing_z", url="a"),
        entry("numbered", articleno="5", url="z"),
        entry("missing_no_url"),
    ]
    # missing/malformed articleno values are all treated alike, so the
    # malformed text "abc" does not affect where junk_b lands
    assert written_ids(entries) == [
        "numbered", "missing_no_url", "empty_a", "missing_z", "junk_b",
    ]


def test_equal_articleno_falls_through_to_url():
    entries = [entry("x", articleno="1", url="b"), entry("y", articleno="1", url="a")]
    assert written_ids(entries) == ["y", "x"]


def test_id_order_is_unchanged():
    entries = [entry("nime_10", articleno="1"), entry("nime_2", articleno="2")]
    assert written_ids(entries, order=("ID",)) == ["nime_10", "nime_2"]


def test_no_order_keeps_file_order():
    entries = [entry(f"p{n}", articleno=str(n)) for n in (3, 1, 2)]
    assert written_ids(entries, order=None) == ["p3", "p1", "p2"]


def test_order_setting_is_restored_after_write():
    written_ids([entry("a", articleno="1")])
    assert utils.writer.order_entries_by == ("articleno", "url", "ID")


@pytest.mark.parametrize("path", sorted(utils.PAPER_PROC.glob("*.bib")))
def test_paper_proceedings_round_trip_in_numeric_order(path):
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    with open(path) as f:
        db = bibtexparser.load(f, parser)
    reparsed = bibtexparser.loads(utils.writer.write(db))
    numbers = [int(e["articleno"]) for e in reparsed.entries
               if e.get("articleno", "").strip().isdecimal()]
    assert numbers == sorted(numbers)
    assert len(reparsed.entries) == len(db.entries)
