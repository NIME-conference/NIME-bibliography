# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A data repository, not an application. The BibTeX files under `paper_proceedings/`,
`music_proceedings/`, `installation_proceedings/` and `alt_proceedings/` are the canonical
source of record for every NIME conference publication. `nime_bib/` is a small Click CLI that
collates and reformats them; everything else exists to serve the data.

Downstream consumers: the GitHub Action builds `release/` and publishes it to GitHub Pages
(<https://nime-conference.github.io/NIME-bibliography/>); the separate `nime-website` repo
pulls those YAML files to generate <https://www.nime.org/archives/>. Breaking the collate
step breaks the public archive.

## Commands

```sh
poetry install                      # setup
make                                # build all of release/ (bib, csv, yaml, json + index.html)
make clean                          # rm release/* — required before rebuilding, see gotcha below
poetry run python nime_bib --help   # CLI help
```

CLI subcommands (run from the repo root — paths in `nime_bib/utils.py` are relative to `.`):

```sh
poetry run python nime_bib collate --type paper --format yaml --id_order
poetry run python nime_bib harmonise 2011 --type paper
poetry run python nime_bib find-keys
poetry run python nime_bib add-dois 2026 dois.csv --type paper
poetry run python nime_bib add-dois 2026 translations.csv --translated
poetry run python nime_bib validate            # structural checks, fails the build on errors
poetry run python nime_bib validate --strict   # also fail on content warnings
make && poetry run python nime_bib validate --release   # check the built output too
```

`validate` is the guard rail: `bibtexparser` discards entries it cannot parse
without raising, so `make` alone will build and deploy an archive with a paper
silently missing from it. It runs on every pull request
(`.github/workflows/validate.yml`) and gates the deploy (`static.yml`). Errors
(unparsed entries, duplicate keys across files) fail the build; warnings
(missing fields, unconverted LaTeX in the built output) are pre-existing and
tracked as issues.

There is no test suite and no linter configured, despite the pytest dev dependency.

## Gotchas

- **`make` is stale-blind.** Targets are real file paths in `release/`, which is gitignored
  but persists locally. If `release/nime_papers.yaml` exists, `make` will not regenerate it
  after a `.bib` edit. Always `make clean` first when verifying a data change.
- **`nime_bib` is not a package import.** `__main__.py` does `import utils`, `import
  latex_accents` — bare top-level imports that only resolve because Python puts the
  `nime_bib/` directory on `sys.path` when run as `python nime_bib`. Don't "fix" these to
  relative imports without changing the invocation everywhere (Makefile, CI, README).
- **`scripts/` is an archive of one-off tooling**, not a maintained library. The per-year
  `20XXcsv2bib.py` scripts have hardcoded paths, editor names and key prefixes at the top and
  are meant to be copied and edited for a new conference edition. `scripts/utils.py` and
  `scripts/edit_bibtex_file.py` are an older duplicate of the `nime_bib` code and are not
  wired into the build. README refers to `scripts/harmonise_bibtex_file.py`, which no longer
  exists — `nime_bib harmonise` replaced it.

## BibTeX conventions

- Canonical field list and order live in `FIELD_ORDER` in `nime_bib/utils.py`; the README
  documents the same template. Anything written back through `utils.writer` is reformatted
  to that order with two-space indentation.
- Entry keys: `nime<year>_<n>` for papers, `nime<year>_music_<n>`, `nime<year>_alt_<n>`.
  Keys must be globally unique across all proceedings files (`find-keys` helps audit).
- Within a year's file, entries are ordered by page/article number.
- Special characters go in the `.bib` files as UTF-8, not LaTeX escapes. `collate` converts
  any remaining LaTeX accents to UTF-8 for the csv/yaml/json outputs (via `latex_accents.py`
  and `latex_symbols.py`) but deliberately preserves them in the combined `.bib`, and warns
  in red about backslashes it could not resolve.
- `harmonise` was written to bring pre-2024 files up to standard; per its own docstring, do
  not run it on new editions' files.
- Translations are stored as a flat `translations = {LANG, DOI, TITLE, LANG, DOI, TITLE, ...}`
  field on the base entry, added by `add-dois --translated`. That mode never touches `doi`.

## File naming

`nime_bib/utils.py` resolves proceedings by convention, so new files must match exactly:
`paper_proceedings/nime{year}.bib`, `music_proceedings/nime{year}_music.bib`,
`installation_proceedings/nime{year}_installations.bib`, `alt_proceedings/nime{year}_alt.bib`.
A new type also needs entries in `collated_path`, `path_for_proc`, `glob_for_proc`, the
`--type` Click choices, the `Makefile`, and `scripts/create_release_index.sh`.
