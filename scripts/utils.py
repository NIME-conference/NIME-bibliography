"""Deprecated: re-exports nime_bib/utils.py, the canonical field order and
writer, so that older notebooks in this directory that `import utils` keep
working. This used to be a separate copy that drifted out of date (#105).
New code should use nime_bib/utils.py directly.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "nime_bib_utils",
    Path(__file__).resolve().parents[1] / "nime_bib" / "utils.py")
_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils)

globals().update(
    {k: v for k, v in vars(_utils).items() if not k.startswith("__")})
