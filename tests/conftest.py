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
def archive(cli_module, tmp_path, monkeypatch):
    """An empty proceedings archive in a temporary directory.

    The tool resolves every path from utils.BASE_PATH (the repository root),
    so this points those paths at the temporary directory instead, and also
    changes into it so tests can open release files by relative path.
    Returns a function that writes a .bib file into it.
    """
    utils = sys.modules["utils"]
    proc_dirs = {"PAPER_PROC": "paper_proceedings",
                 "MUSIC_PROC": "music_proceedings",
                 "INSTALL_PROC": "installation_proceedings",
                 "ALT_PROC": "alt_proceedings"}
    for name, d in proc_dirs.items():
        (tmp_path / d).mkdir()
        monkeypatch.setattr(utils, name, tmp_path / d)
    monkeypatch.setattr(utils, "BASE_PATH", tmp_path)
    monkeypatch.setattr(utils, "RELEASE_PATH", tmp_path / "release")
    monkeypatch.chdir(tmp_path)

    def add_bib(relpath, text):
        (tmp_path / relpath).write_text(text, encoding="utf-8")

    return add_bib
