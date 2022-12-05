import click
import bibtexparser
import utils
import pandas as pd
import pyaml

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

  if format == "bib":
    set_id_order(id_order)
    with open(output_file, 'w') as bibtex_file:
        bibtex_file.write(utils.writer.write(bd)) 
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
