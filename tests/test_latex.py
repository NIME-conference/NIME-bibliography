"""Tests for the LaTeX symbol and brace handling used by collate (#101)."""

import sys

import pytest

from nime_bib import latex_symbols


@pytest.mark.parametrize("text, expected", [
    # control words are replaced on their own ...
    (r"Str\o m", "Strø m"),
    (r"{\o}", "ø"),
    (r"Fl\o and Hans", "Flø and Hans"),
    (r"\aa", "å"),
    (r"Stra{\ss}e", "Straße"),
    (r"music\ae (Paris)", "musicæ (Paris)"),
    (r"caf\'e \& bar", r"caf\'e & bar"),
    (r"J\'er\^ome", r"J\'erôme"),
    (r"100\%", "100%"),
    (r"$\times$", "×"),
    # ... but not inside a longer control word
    (r"\omega", r"\omega"),
    (r"\overline{x}", r"\overline{x}"),
    (r"\aardvark", r"\aardvark"),
    (r"\ssharp", r"\ssharp"),
    (r"\texttt{code}", r"\texttt{code}"),
])
def test_replace_symbols(text, expected):
    assert latex_symbols.replace_symbols(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("{Big} {Letters}", "Big Letters"),
    ("{{nested}}", "nested"),
    ("$f_{0}$", "$f_{0}$"),
    (r"$\{1,2\}$", r"$\{1,2\}$"),
    ("the {pitch} $f_{0}$ of {X}", "the pitch $f_{0}$ of X"),
    ("costs $5 to {over} $10", "costs $5 to {over} $10"),
    ("unterminated $x_{1}", "unterminated $x_1"),
    ("no braces", "no braces"),
])
def test_clean_braces(text, expected):
    assert latex_symbols.clean_braces(text) == expected
