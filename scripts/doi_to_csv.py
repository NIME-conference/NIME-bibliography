"""
Opens any bibtex file in the present directory and extracts any present DOI.
The ENTRYID and doi are saved in a CSV file (one per bibtex file)
Also lets you know if there are any missing DOIs!
"""
import glob
import bibtexparser
import pandas as pd

bibfiles = []
bibdatabases = {}
for file in glob.glob("*.bib"):
    bibfiles.append(file)

id_to_doi_dfs = []

for bf in bibfiles:
    print(bf)
    with open(bf) as bibtex_file:
        bib_database = bibtexparser.bparser.BibTexParser(common_strings=True).parse_file(bibtex_file)
    bibdatabases[bf] = bib_database
    id_to_doi = {}    
    for e in bib_database.entries:
        try:
            if e['doi'] is not None:
                id_to_doi[e['ID']] = e['doi']
        except:
            print("No DOI for:", e['ID'])
    id_to_doi_df = pd.DataFrame.from_dict(id_to_doi, orient='index', columns=['doi'])
    id_to_doi_df['ID'] = id_to_doi_df.index
    id_to_doi_df.to_csv(bf[:-4]+".csv", index=False)
    id_to_doi_dfs.append(id_to_doi_df)
    
id_to_doi_df = pd.concat(id_to_doi_dfs)
