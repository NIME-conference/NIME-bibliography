import importlib.util
import sys
from pathlib import Path

import pytest

NIME_BIB_DIR = Path(__file__).resolve().parent.parent / "nime_bib"


@pytest.fixture(scope="session")
def cli_module():
    """The nime_bib command line module.

    nime_bib/__main__.py imports its siblings as top-level modules (it is run
    as `python nime_bib`), so load it the same way rather than as a package.
    """
    sys.path.insert(0, str(NIME_BIB_DIR))
    spec = importlib.util.spec_from_file_location("nime_bib_cli", NIME_BIB_DIR / "__main__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def archive(tmp_path, monkeypatch):
    """An empty proceedings archive in a temporary directory.

    The tool resolves every path relative to the working directory, so this
    changes into it. Returns a function that writes a .bib file into it.
    """
    for d in ("paper_proceedings", "music_proceedings",
              "installation_proceedings", "alt_proceedings"):
        (tmp_path / d).mkdir()
    monkeypatch.chdir(tmp_path)

    def add_bib(relpath, text):
        (tmp_path / relpath).write_text(text, encoding="utf-8")

    return add_bib
