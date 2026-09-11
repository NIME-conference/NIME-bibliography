import click
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding
import utils
import pandas as pd
import pyaml
import latex_accents
import latex_symbols
import csv
import re
import yaml


def set_id_order(id_order):
  """Sets the entry order for the bibtex writer.

  id_order=True sorts entries by their BibTeX key. Otherwise the writer's
  default (article number, url, key) is used. Note the trailing comma:
  ("ID") is just the string "ID", which bibtexparser would read as the two
  field names "I" and "D" and silently not sort at all.
  """
  if id_order:
      utils.writer.order_entries_by = ("ID",)
      click.secho("ordering by ID")
  else:
      click.secho(f"Using default order: {utils.writer.order_entries_by}")


def preserve_file_order():
  """Makes the bibtex writer keep entries in the order they were parsed.

  The source files are maintained in page/article order, and the collated
  output concatenates them year by year, so this is the canonical order.
  """
  utils.writer.order_entries_by = None


@click.command()
@click.argument('year', type=click.INT)
@click.option(
    "--type",
    type=click.Choice(["paper", "music", "installation", "alt"]),
    default="paper",
    help="type of proceedings"
)
@click.option(
    "--id_order",
    "-I",
    is_flag=True,
    default=False,
    help="sorts the output by entry ID/key (default: sort by article/page number)"
)
def harmonise(year, type, id_order):
  """Loads a NIME proceedings BibTeX file for a given YEAR and harmonises the
  fields and order.

  This was specifically used to update older NIME .bib files to current
  standards. From 2024, this should not be used on new .bib files for new
  NIME editions unless it is updated to meet current standards in the bib
  files (see README.md).
  """
  nime_file = utils.path_for_proc(year, type)

  click.secho(f"Going to load: {nime_file}, hope that's ok.")
  with open(nime_file) as bibtex_file:
    bib_database = bibtexparser.bparser.BibTexParser(
        common_strings=True,
        customization=homogenize_latex_encoding
    ).parse_file(bibtex_file)
  click.secho(f"Loaded {len(bib_database.entries)} entries.")
  
  set_id_order(id_order)
  # Write back to the bibtex file
  with open(nime_file, 'w') as bibtex_file:
      bibtex_file.write(utils.writer.write(bib_database))

  click.secho(f"Saved new entried to: {nime_file}, hope that's ok.", fg="green")


@click.command()
@click.option(
    "--type",
    type=click.Choice(["paper", "music", "installation", "alt"]),
    default="paper",
    help="type of proceedings"
)
@click.option(
    "--format",
    "-F",
    type=click.Choice(["bib", "csv", "yaml", "json"]),
    default="bib",
    help="format of output"
)
def collate(type, format):
  """Collates all NIME proceedings of a certain type and saves to an output
  file.

  Entries are output year by year (files sorted by name) and, within a
  year, in the order they appear in the source file, which is page/article
  order. The order is the same for every output format and every platform,
  so two builds of the same sources can be compared byte for byte.
  """
  output_file = utils.collated_path(type, format)
  bibfiles = utils.glob_for_proc(type)
  bib_entries = []

  with click.progressbar(bibfiles) as bar:
    for bf in bar:
      with open(bf, encoding="utf-8") as bibtex_file:
        bd = bibtexparser.bparser.BibTexParser(
            common_strings=True
        ).parse_file(bibtex_file)
        bib_entries.extend(bd.entries)

  # set up collated database
  bd = bibtexparser.bibdatabase.BibDatabase()
  bd.entries = bib_entries
  accent_converter = latex_accents.AccentConverter()

  # BibTex Output (preserve latex accents)
  if format == "bib":
    preserve_file_order()
    with open(output_file, 'w', encoding="utf-8") as bibtex_file:
        bibtex_file.write(utils.writer.write(bd))
  
  # Other formats (convert accents to UTF8)
  for e in bib_entries:
    # add a "bibtex" field:
    small_bd = bibtexparser.bibdatabase.BibDatabase()
    small_bd.entries = [e]
    bibtex_str = bibtexparser.dumps(small_bd)
    e['bibtex'] = bibtex_str

    # Convert LaTeX in the published text fields to UTF-8. Each field is
    # handled independently: an entry with no abstract must still have its
    # title and author converted (this used to `continue` on the missing
    # abstract and skip them, see issue #98).
    for field in ("abstract", "title", "author"):
      _convert_entry_field(e, field, accent_converter)

    try:
      if '\\' in e['ID']:
        e['ID'] = accent_converter.decode_Tex_Accents(
            e['ID'],
            utf8_or_ascii=2
        )
        click.secho(f"Fixed {e['ID']} ID: {e['ID']}", fg="red")
    except Exception as exc:
      click.secho(f"Exception: {exc}", fg="red")
      click.secho(f"Entry: {e}", fg="blue")

  if format == "csv":
    df = pd.DataFrame.from_records(bib_entries)
    df.to_csv(output_file)
  if format == "yaml":
    with open(output_file, 'w') as f:
      pyaml.dump(bib_entries, f, vspacing=[2, 0])
  if format == "json":
    df = pd.DataFrame.from_records(bib_entries)
    df.to_json(output_file)
  
  click.secho(
      f"Saved {len(bd.entries)} entries to: {output_file}, hope that's ok.",
      fg="green"
  )


@click.command()
def find_keys():
  """Finds all BibTeX keys used in all available proceedings files.
  """
  bibfiles = []
  bibdatabases = {}
  for file in utils.glob_for_proc("paper"):
      bibfiles.append(file)
  for file in utils.glob_for_proc("music"):
      bibfiles.append(file)
  for file in utils.glob_for_proc("installation"):
      bibfiles.append(file)
  for file in utils.glob_for_proc("alt"):
      bibfiles.append(file)
  
  def add_keys(e, k):
      e_keys = set(e.keys())
      k |= e_keys

  keys = set()

  with click.progressbar(bibfiles) as bar:
    for bf in bar:
        with open(bf) as bibtex_file:
            bib_database = bibtexparser.bparser.BibTexParser(
                common_strings=True
            ).parse_file(bibtex_file)
        bibdatabases[bf] = bib_database
        for e in bib_database.entries:
            add_keys(e, keys)
  
  entry_keys = list(keys)
  entry_keys.sort()
  click.secho(entry_keys)


def _strip_pdf_suffix(key: str) -> str:
  """Remove a trailing .pdf (case-insensitive) from a key, if present."""
  key = key.strip()
  if key.lower().endswith(".pdf"):
    return key[:-4]
  return key


@click.command()
@click.argument('year', type=click.INT)
@click.argument('csvfile', type=click.STRING)
@click.option(
    "--type",
    type=click.Choice(["paper", "music", "installation", "alt"]),
    default="paper",
    help="type of proceedings"
)
@click.option(
    "--translated",
    is_flag=True,
    default=False,
    help=(
        "interpret CSV keys as KEY_LANGUAGE.pdf and add "
        "translations={LANG, DOI, TITLE, ...} to the BibTeX entries"
    )
)
def add_dois(year, csvfile, type, translated):
  """Adds DOIs (and optionally translation metadata) to a year of NIME proceedings.

  CSV 'key' values are expected to include a '.pdf' suffix and it is
  removed before matching.

  Normal mode:
      - CSV 'key' (without '.pdf') must match the BibTeX 'ID' exactly.
      - Adds/overwrites the 'doi' field in each matching entry.

  Translation mode (with --translated):

      Expected CSV header (minimum):

          key,zenodo_deposition_id,doi,title

      where:
        - 'key' is of the form KEY_LANGUAGE.pdf (e.g. nime2026_27_Spanish.pdf),
        - 'doi' is the DOI for that translated version,
        - 'title' is the translated title for that language.

      After removing '.pdf', the script:
        - uses KEY (before the last '_') as the BibTeX 'ID'
        - uses LANGUAGE (after the last '_') as a language label.

      It then adds a single field to the base BibTeX entry:

          translations = {LANG1, DOI1, TITLE1, LANG2, DOI2, TITLE2, ...}

      It does NOT add or modify the standard 'doi' field.
  """
  nime_file = utils.path_for_proc(year, type)
  # Load the NIME bibtex file
  click.secho(f"Going to load: {nime_file}, hope that's ok.")
  with open(nime_file) as bibtex_file:
    bib_database = bibtexparser.bparser.BibTexParser(
        common_strings=True
    ).parse_file(bibtex_file)
  click.secho(f"Loaded {len(bib_database.entries)} entries.")
  
  # Load the CSV file and apply logic depending on mode
  with open(csvfile, newline='') as doi_file:
    reader = csv.DictReader(doi_file)

    if not translated:
      # Normal mode: keys in CSV (minus '.pdf') match BibTeX IDs exactly
      key_to_doi = {}
      for row in reader:
        raw_key = row['key']
        clean_key = _strip_pdf_suffix(raw_key)
        key_to_doi[clean_key] = row['doi']

      # Add the DOIs
      for e in bib_database.entries:
        click.secho(f"Finding DOI for {e['ID']}", fg='yellow')
        try:
          e['doi'] = key_to_doi[e['ID']]
        except KeyError:
          click.secho(
              f"No DOI found for {e['ID']} in CSV (leaving entry unchanged)",
              fg='red'
          )

    else:
      # Translation mode, using CSV from nime_zenodo_upload --title.
      # Expected CSV header (minimum):
      #   key,zenodo_deposition_id,doi,title
      #
      # Example rows:
      #   nime2026_27_Spanish.pdf,20784032,10.5281/zenodo.20784032,Tejer antes...
      #   nime2026_27_Italian.pdf,20784032,10.5281/zenodo.20784033,Tessere prima...
      #
      basekey_to_translations = {}

      for row in reader:
        raw_key = row['key']                     # e.g. "nime2026_27_Spanish.pdf"
        key_no_pdf = _strip_pdf_suffix(raw_key)  # "nime2026_27_Spanish"
        doi_value = row['doi']                   # e.g. "10.5281/zenodo.20784032"
        # Use the 'title' column from the CSV as the translated title
        title_value = row.get('title', '').strip()

        # Split into base key and language by the last underscore
        if '_' not in key_no_pdf:
          click.secho(
              f"Skipping CSV row with key '{raw_key}' "
              f"(no '_' to separate language after stripping '.pdf')",
              fg='red'
          )
          continue

        base_key, language = key_no_pdf.rsplit('_', 1)
        base_key = base_key.strip()
        language = language.strip()

        if base_key not in basekey_to_translations:
          basekey_to_translations[base_key] = []
        basekey_to_translations[base_key].append({
            "language": language,
            "doi": doi_value,
            "title": title_value,
        })

      # Add translation-related field to BibTeX entries
      for e in bib_database.entries:
        entry_id = e['ID']
        click.secho(f"Processing translations for {entry_id}", fg='yellow')

        if entry_id not in basekey_to_translations:
          # No translation info for this entry; leave unchanged
          continue

        translations = basekey_to_translations[entry_id]

        # Build translations string: LANGUAGE, DOI, TITLE, LANGUAGE, DOI, TITLE, ...
        translations_parts = []

        for item in translations:
          lang = item["language"]
          doi = item["doi"]
          title = item["title"]

          # Always include language and doi; include title (can be empty string if absent)
          translations_parts.append(lang)
          translations_parts.append(doi)
          translations_parts.append(title)

        if translations_parts:
          translations_value = ", ".join(translations_parts)
          e['translations'] = translations_value
          click.secho(
            f"Added translations field for {entry_id}: "
            f"{{{translations_value}}}",
            fg='green'
          )

        # IMPORTANT: In translation mode we do NOT add or modify e['doi'].

  # Write back to the bibtex file
  preserve_file_order()
  with open(nime_file, 'w') as bibtex_file:
      bibtex_file.write(utils.writer.write(bib_database))

  click.secho(f"Saved new entries to: {nime_file}, hope that's ok.", fg="green")


def _convert_latex(text, accent_converter):
  """Applies the same LaTeX-to-UTF8 conversion that collate uses.

  Kept in step with collate so that validate reports what would actually
  reach the published files, not what the source happens to contain.
  """
  text = accent_converter.decode_Tex_Accents(text, utf8_or_ascii=1)
  text = latex_symbols.replace_symbols(text)
  text = accent_converter.decode_Tex_Accents(text, utf8_or_ascii=1)
  return text


def _convert_entry_field(entry, field, accent_converter):
  """Converts LaTeX in one text field of an entry to UTF-8, in place.

  Does nothing if the entry lacks the field. Warns in red about backslashes
  that survive conversion, since those reach the published files as-is.
  """
  value = entry.get(field)
  if value is None:
    return
  if '\\' in value:
    value = _convert_latex(value, accent_converter)
  if '\\' in value:
    click.secho(f"{entry['ID']} {field} still contains backslashes!", fg="red")
    click.secho(f"{entry['ID']} {field}: {value}", fg="yellow")
  entry[field] = latex_symbols.clean_braces(value)


def _raw_entry_keys(text):
  """Returns the BibTeX keys of every entry header found in raw file text.

  Deliberately independent of bibtexparser: this is what we compare the
  parsed result against, so that an entry the parser quietly discards
  still shows up here.
  """
  return re.findall(r'^@\w+\s*\{\s*([^,\s]+)\s*,', text, re.M)


@click.command()
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="treat warnings as errors (exit non-zero on any problem)"
)
@click.option(
    "--release",
    is_flag=True,
    default=False,
    help=(
        "also check the built files in release/ (run `make` first). Catches "
        "conversion faults that only appear in the collated output."
    )
)
def validate(strict, release):
  """Checks every proceedings file for problems that would corrupt the
  published archive.

  Errors are structural faults that silently lose or confuse data:
  entries the BibTeX parser discards, and keys reused across files.
  These fail the build.

  Warnings are content problems that are tracked as known issues and do
  not fail the build unless --strict is given.
  """
  errors = []
  warnings = []
  seen_keys = {}
  accent_converter = latex_accents.AccentConverter()
  total_raw = 0
  n_files = 0

  for _proc_type, path in utils.all_proc_files():
    n_files += 1
    text = path.read_text()
    raw_keys = _raw_entry_keys(text)
    bib_database = bibtexparser.bparser.BibTexParser(
        common_strings=True
    ).parse(text)
    parsed_keys = [e['ID'] for e in bib_database.entries]
    total_raw += len(raw_keys)

    # Entries the parser silently dropped. bibtexparser turns an entry it
    # cannot parse into a comment rather than raising, so a missing comma
    # removes a paper from the archive with no other signal.
    parsed_set = set(parsed_keys)
    for key in raw_keys:
      if key not in parsed_set:
        errors.append(
            f"{path}: entry '{key}' was not parsed - it is almost certainly "
            f"malformed (a missing comma after a field is the usual cause) "
            f"and will be missing from the published archive"
        )
    for comment in bib_database.comments:
      first_line = comment.strip().splitlines()[0][:60]
      errors.append(
          f"{path}: unparsed content treated as a comment, starting "
          f"'{first_line}'"
      )

    # Keys must be unique across every proceedings file, not just within one.
    for key in parsed_keys:
      if key in seen_keys:
        errors.append(
            f"{path}: key '{key}' is already used in {seen_keys[key]}"
        )
      else:
        seen_keys[key] = path

    for entry in bib_database.entries:
      key = entry['ID']

      for field in utils.REQUIRED_FIELDS:
        if not entry.get(field, "").strip():
          warnings.append(f"{path}: {key} has no {field}")

      # LaTeX escapes are fine in the source files; what matters is
      # whether collate can convert them. Run the same conversion here and
      # warn only about what it fails to resolve, since that is what ends
      # up on the website.
      for field in utils.PUBLISHED_TEXT_FIELDS:
        value = entry.get(field, "")
        if '\\' in value and '\\' in _convert_latex(value, accent_converter):
          warnings.append(
              f"{path}: {key} has LaTeX in {field} that collate cannot convert"
          )

      if not entry.get("url", "").strip() and not entry.get("doi", "").strip():
        warnings.append(f"{path}: {key} has neither url nor doi")

  if release:
    for path in sorted(utils.RELEASE_PATH.glob("*.yaml")):
      for entry in yaml.safe_load(path.read_text()) or []:
        for field in utils.PUBLISHED_TEXT_FIELDS:
          # The 'bibtex' field is a raw dump and is excluded on purpose.
          if '\\' in entry.get(field, ""):
            warnings.append(
                f"{path}: {entry.get('ID', '?')} was published with "
                f"unconverted LaTeX in {field}"
            )

  click.secho(
      f"Checked {total_raw} entries in {len(seen_keys)} unique keys "
      f"across {n_files} files."
  )

  if warnings:
    click.secho(f"\n{len(warnings)} warning(s):", fg="yellow")
    for w in warnings:
      click.secho(f"  {w}", fg="yellow")

  if errors:
    click.secho(f"\n{len(errors)} error(s):", fg="red")
    for e in errors:
      click.secho(f"  {e}", fg="red")

  if errors or (strict and warnings):
    click.secho("\nValidation failed.", fg="red")
    raise SystemExit(1)

  if warnings:
    click.secho(
        "\nValidation passed (warnings are tracked as known issues).",
        fg="green"
    )
  else:
    click.secho("\nValidation passed.", fg="green")


@click.group()
def cli():
    pass


cli.add_command(harmonise)
cli.add_command(find_keys)
cli.add_command(collate)
cli.add_command(add_dois)
cli.add_command(validate)

if __name__ == '__main__':
    cli()
