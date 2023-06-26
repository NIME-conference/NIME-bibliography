import click
import bibtexparser
import utils
import pandas as pd
import pyaml
import latex_accents
import latex_symbols

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
@click.option("--type", type=click.Choice(["papers", "music", "installations"]), default="papers", help="type of proceeding")
@click.option("--id_order", "-I", is_flag=True, default=False, help="sorts the output by entry ID/key (default: sort by article/page number)")
def harmonise(year, type, id_order):
  """Loads a NIME proceedings BibTeX file for a given YEAR and harmonises the fields and order.
  """
  nime_file = utils.path_for_proc(year, type)

  click.secho(f"Going to load: {nime_file}, hope that's ok.")
  with open(nime_file) as bibtex_file:
    bib_database = bibtexparser.bparser.BibTexParser(common_strings=True).parse_file(bibtex_file)
  click.secho(f"Loaded {len(bib_database.entries)} entries.")
  
  set_id_order(id_order)
  # Write back to the bibtex file
  with open(nime_file, 'w') as bibtex_file:
      bibtex_file.write(utils.writer.write(bib_database))

  click.secho(f"Saved new entried to: {nime_file}, hope that's ok.", fg="green")

@click.command()
@click.option("--type", type=click.Choice(["papers", "music", "installations"]), default="papers", help="type of proceeding")
@click.option("--id_order", "-I", is_flag=True, default=False, help="sorts the output by entry ID/key (default: sort by article/page number)")
@click.option("--format", "-F", type=click.Choice(["bib", "csv", "yaml", "json"]), default="bib", help="format of output")
def collate(type, id_order, format):
  """Collates all NIME proceedings of a certain type and saves to an output file.
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
        bd = bibtexparser.bparser.BibTexParser(common_strings=True).parse_file(bibtex_file)
        bib_databases.append(bd)
        bib_entries.extend(bd.entries)
  
  # set up collated database
  bd.entries = bib_entries
  bd._make_entries_dict()
  accent_converter = latex_accents.AccentConverter()
  # output_string = accent_converter.decode_Tex_Accents(input_string, utf8_or_ascii=1) # replace latex accents with UTF8

  # BibTex Output (preserve accents)
  if format == "bib":
    set_id_order(id_order)
    with open(output_file, 'w') as bibtex_file:
        bibtex_file.write(utils.writer.write(bd)) 
  
  # Other formats (convert accents)
  print(bib_entries[0])
  for e in bib_entries:
    # look at entries with \
    # look at abstract, title, author
    try:
      if '\\' in e['abstract']:
        e['abstract'] = latex_symbols.replace_symbols(e['abstract'])
        e['abstract'] = accent_converter.decode_Tex_Accents(e['abstract'], utf8_or_ascii=1)
        # click.secho(f"Fixed {e['ID']} abstract: {e['abstract']}", fg="yellow")
        if '\\' in e['abstract']:
          click.secho(f"{e['ID']} abstract still contains backslashes!", fg="red")
          click.secho(f"{e['ID']} Abstract: {e['abstract']}", fg="yellow")
      if '\\' in e['title']:
        e['title'] = latex_symbols.replace_symbols(e['title'])
        e['title'] = accent_converter.decode_Tex_Accents(e['title'], utf8_or_ascii=1)
        # click.secho(f"Fixed {e['ID']} title: {e['title']}", fg="yellow")
        if '\\' in e['title']:
          click.secho(f"{e['ID']} title still contains backslashes!", fg="red")
          click.secho(f"{e['ID']} Title: {e['title']}", fg="yellow")
      if '\\' in e['author']:
        e['author'] = latex_symbols.replace_symbols(e['author'])
        e['author'] = accent_converter.decode_Tex_Accents(e['author'], utf8_or_ascii=1)
        # click.secho(f"Fixed {e['ID']} author: {e['author']}", fg="yellow")
        if '\\' in e['author']:
          click.secho(f"{e['ID']} author still contains backslashes!", fg="red")
          click.secho(f"{e['ID']} Author: {e['author']}", fg="yellow")
      if '\\' in e['ID']:
        e['ID'] = accent_converter.decode_Tex_Accents(e['ID'], utf8_or_ascii=2)
        click.secho(f"Fixed {e['ID']} ID: {e['ID']}", fg="red")
    except Exception as exc:
      if "abstract" not in str(exc):
        click.secho(f"Exception: {exc}", fg="red")
        click.secho(f"Entry: {e}", fg="blue")

  if format == "csv":
    df = pd.DataFrame.from_records(bib_entries)
    df.to_csv(output_file)
  if format == "yaml":
    with open(output_file, 'w') as f:
      pyaml.dump(bib_entries, f, vspacing=[2,0])
  if format == "json":
    df = pd.DataFrame.from_records(bib_entries)
    df.to_json(output_file)
  
  click.secho(f"Saved {len(bd.entries)} entries to: {output_file}, hope that's ok.", fg="green")


@click.command()
def find_keys():
  """Finds all BibTeX keys used in all available proceedings files.
  """
  bibfiles = []
  bibdatabases = {}
  for file in utils.glob_for_proc("papers"):
      bibfiles.append(file)
  for file in utils.glob_for_proc("music"):
      bibfiles.append(file)
  for file in utils.glob_for_proc("installations"):
      bibfiles.append(file)
  
  def add_keys(e, k):
      e_keys = set(e.keys())
      k |= e_keys

  keys = set()

  with click.progressbar(bibfiles) as bar:
    for bf in bar:
        with open(bf) as bibtex_file:
            bib_database = bibtexparser.bparser.BibTexParser(common_strings=True).parse_file(bibtex_file)
        bibdatabases[bf] = bib_database
        for e in bib_database.entries:
            add_keys(e, keys)
  
  entry_keys = list(keys)
  entry_keys.sort()
  click.secho(entry_keys)


@click.group()
def cli():
    pass

cli.add_command(harmonise)
cli.add_command(find_keys)
cli.add_command(collate)

if __name__ == '__main__':
    cli()

