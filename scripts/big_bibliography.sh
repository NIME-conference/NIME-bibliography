#!/bin/sh
echo "---\ntitle: Complete NIME Proceedings\nnocite: '@*'\n...\n" | pandoc --standalone --citeproc --csl apa.csl --output=proceedings.pdf --pdf-engine=xelatex --bibliography=../release/nime_papers.bib
