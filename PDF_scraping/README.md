These files contains code extracting keywords and abstract from papers presented at the NIME conferences. 
The Python based scripts tries to open the pdf files, then read them the text and the meta-data Pdf-destiller. 
These data are then printed in a XML-stuctured document which is saved. 
At one point these data should be fed into a bibtex-file.

Good to know: 
* The bibtex files are contained within the nime_archive/nime/bibtex folder. They do all have .bib suffixes, but be aware, there is also another 'proposal.bib' with same suffix. 
* The .pdf files can be found in nime_archive/web/XXXX (where the XXXX are the year in question. From 2001 to 2012). 
* The .pdfs are not found in the git repository (they are too big and hence .gitignore d)