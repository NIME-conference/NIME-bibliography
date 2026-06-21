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


def set_id_order(id_order):
  """Sets the order for the bibtex writer
  """
  # set ordering property:
  if (id_order):
      utils.writer.order_entries_by = ("ID")
      click.secho("ordering by ID")
  else:
      click.secho(f"Using default order: {utils.writer.order_entries_by}")
  # else, canonical order: #utils.writer.order_entries_by = ("articleno", "url", "ID")


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
    "--id_order",
    "-I",
    is_flag=True,
    default=False,
    help="sorts the output by entry ID/key (default: sort by article/page number)"
)
@click.option(
    "--format",
    "-F",
    type=click.Choice(["bib", "csv", "yaml", "json"]),
    default="bib",
    help="format of output"
)
def collate(type, id_order, format):
  """Collates all NIME proceedings of a certain type and saves to an output
  file.
  """
  output_file = utils.collated_path(type, format)
  bibfiles = []
  bib_entries = []
  bib_databases = []
  for file in utils.glob_for_proc(type):
      bibfiles.append(file)

  with click.progressbar(bibfiles) as bar:
    for bf in bar:
      with open(bf) as bibtex_file:
        bd = bibtexparser.bparser.BibTexParser(
            common_strings=True
        ).parse_file(bibtex_file)
        bib_databases.append(bd)
        bib_entries.extend(bd.entries)
  
  # set up collated database
  bd.entries = bib_entries
  accent_converter = latex_accents.AccentConverter()

  # BibTex Output (preserve latex accents)
  if format == "bib":
    set_id_order(id_order)
    with open(output_file, 'w') as bibtex_file:
        bibtex_file.write(utils.writer.write(bd)) 
  
  # Other formats (convert accents to UTF8)
  for e in bib_entries:
    # add a "bibtex" field:
    small_bd = bibtexparser.bibdatabase.BibDatabase()
    small_bd.entries = [e]
    bibtex_str = bibtexparser.dumps(small_bd)
    e['bibtex'] = bibtex_str

    # look at entries with \
    # look at abstract, title, author
    try: 
      if '\\' in e['abstract']:
        e['abstract'] = accent_converter.decode_Tex_Accents(
            e['abstract'],
            utf8_or_ascii=1
        )
        e['abstract'] = latex_symbols.replace_symbols(e['abstract'])
        e['abstract'] = accent_converter.decode_Tex_Accents(
            e['abstract'],
            utf8_or_ascii=1
        )  # do this twice to catch them all.
      if '\\' in e['abstract']:
        click.secho(
            f"{e['ID']} abstract still contains backslashes!",
            fg="red"
        )
        click.secho(f"{e['ID']} Abstract: {e['abstract']}", fg="yellow")
      e['abstract'] = latex_symbols.clean_braces(e['abstract'])
    except Exception:
      continue

    try:
      if '\\' in e['title']:
        e['title'] = accent_converter.decode_Tex_Accents(
            e['title'],
            utf8_or_ascii=1
        )
        e['title'] = latex_symbols.replace_symbols(e['title'])
        e['title'] = accent_converter.decode_Tex_Accents(
            e['title'],
            utf8_or_ascii=1
        )  # do this twice to catch them all.
      if '\\' in e['title']:
        click.secho(
            f"{e['ID']} title still contains backslashes!",
            fg="red"
        )
        click.secho(f"{e['ID']} Title: {e['title']}", fg="yellow")
      e['title'] = latex_symbols.clean_braces(e['title'])
    except Exception as exc:
      click.secho(f"Exception: {exc}", fg="red")

    try:
      if '\\' in e['author']:
        e['author'] = accent_converter.decode_Tex_Accents(
            e['author'],
            utf8_or_ascii=1
        )
        e['author'] = latex_symbols.replace_symbols(e['author'])
        e['author'] = accent_converter.decode_Tex_Accents(
            e['author'],
            utf8_or_ascii=1
        )  # do this twice to catch them all.
      if '\\' in e['author']:
        click.secho(
            f"{e['ID']} author still contains backslashes!",
            fg="red"
        )
        click.secho(f"{e['ID']} Author: {e['author']}", fg="yellow")
      e['author'] = latex_symbols.clean_braces(e['author'])
    except Exception as exc:
      click.secho(f"Exception: {exc}", fg="red")

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
  set_id_order(True)
  with open(nime_file, 'w') as bibtex_file:
      bibtex_file.write(utils.writer.write(bib_database))

  click.secho(f"Saved new entries to: {nime_file}, hope that's ok.", fg="green")


@click.group()
def cli():
    pass


cli.add_command(harmonise)
cli.add_command(find_keys)
cli.add_command(collate)
cli.add_command(add_dois)

if __name__ == '__main__':
    cli()
