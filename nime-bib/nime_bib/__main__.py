import click
import glob
import bibtexparser
import utils
import sys
# from pathlib import Path

@click.command()
@click.argument('year', type=click.INT)
@click.option("--type", type=click.Choice(["papers", "music", "installations"]), default="papers", help="type of proceeding")
@click.option("--id_order", "-I", is_flag=True, default=False, help="sorts the output by entry ID/key (default: sort by article/page number)")
def harmonise(year, type, id_order):
  """Loads a NIME proceedings BibTeX file for a given YEAR and harmonises the fields and order.
  """
  if type == "papers":
    nime_file = f"../paper_proceedings/nime{year}.bib"
  elif type == "music":
    nime_file = f"../music_proceedings/nime{year}_music.bib"
  elif type == "installations":
    nime_file = f"../installation_proceedings/nime{year}_installations.bib"
  else:
    nime_file = None

  click.secho(f"Going to load: {nime_file}, hope that's ok.")
  with open(nime_file) as bibtex_file:
    bib_database = bibtexparser.bparser.BibTexParser(common_strings=True).parse_file(bibtex_file)
  click.secho(f"Loaded {len(bib_database.entries)} entries.")
  # set ordering property:
  if (id_order):
      utils.writer.order_entries_by = ("ID")
      click.secho("ordering by ID")
  else:
      click.secho(f"Using default order: {utils.writer.order_entries_by}")
  # else, canonical order: #utils.writer.order_entries_by = ("articleno", "url", "ID")

  # Write back to the bibtex file
  with open(nime_file, 'w') as bibtex_file:
      bibtex_file.write(utils.writer.write(bib_database))

  click.secho(f"Saved new entried to: {nime_file}, hope that's ok.", fg="green")


@click.command()
def find_keys():
  """Finds all BibTeX keys used in all available proceedings files.
  """
  bibfiles = []
  bibdatabases = {}
  path = "../paper_proceedings/*.bib"
  for file in glob.glob(path):
      bibfiles.append(file)
  path = "../music_proceedings/*.bib"
  for file in glob.glob(path):
      bibfiles.append(file)
  path = "../installation_proceedings/*.bib"
  for file in glob.glob(path):
      bibfiles.append(file)
      
  def add_keys(e, k):
      e_keys = set(e.keys())
      k |= e_keys

  keys = set()

  for bf in bibfiles:
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

if __name__ == '__main__':
    cli()

