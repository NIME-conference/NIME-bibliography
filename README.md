NIME-bibliography
=================

This is the bibliography files (in BibTeX format) of all publications from the annual [International Conference on New Interfaces for Musical Expression](http://www.nime.org) (NIME). These files are the source for the [NIME proceedings database](http://www.nime.org/archives/). 

The abstracts and keywords have been scraped from the each of the original PDF files using [this script](https://github.com/olovholm/NIME). We have been doing some automatic and manual cleaning up after running the script, but there are still linguistic (and other) errors in the database. Please help us clean it up!

The idea is that keeping the bibliography in an open and accessible format, it can be usable for the community, and it will also be easier to correct errors. 

Merge 
--------

All the individual BibTeX files can be merged into one large file using the following terminal command: 

    cat nime20* > nime.bib

This file is then read by the  WordPress plugin [WP-Publications](http://www.monperrus.net/martin/wp-publications), which is based on [bibtexbrowser](http://www.monperrus.net/martin/bibtexbrowser/). 


Zenodo upload
--------------

The python script in the Zenodo folder (NIME_upload.py) reads a .bib file from the NIME archive and creates a deposition record on the Zenodo website. The metadata from the .bib entries are tied to the article (.pdf file) and are publishedd to Zenodo resulting in the creation of a DOI. When this script is used to upload a new batch of papers the DOI
and file name of each paper are added to the text file NIME_dois.txt. 

- Run: Place script in the directory which contains the .bib file and all .pdf's. Then run using 'python NIME_upload.py'
- Additional files: If a resource contains an additional file that should be uploaded together with the paper this additional file should have the same file name with an additional file01 appended to the end. Zenodo displays the files alphabetically. Today this script only allows for adding one additional file per resource.
- The .bib file: Special charachters in the .bib file should be written in LaTeX code.

Thanks to [Benedikte Wallace](https://www.linkedin.com/in/benedikte-wallace-8b489782/) for developing the Zenodo upload script. 



Contact
-------
The bibliograpy has been uploaded and is currently updated by [Alexander Refsum Jensenius](http://www.hf.uio.no/imv/english/people/aca/alexanje/index.html), University of Oslo, and chair of the [NIME Steering Committee](http://www.nime.org/committee/).