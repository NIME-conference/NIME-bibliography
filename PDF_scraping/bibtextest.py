#!/usr/bin/python
#-*- coding: utf-8


from pybtex.database.input import bibtex
import os

dir_path = r"nime_archive/nime/bibtex/"
bibfiles = []
parser = bibtex.Parser()


      
    
class Bibfile:
  def __init__(self,bibs,name):
    global exception_cnt
    global texts_cnt
    self.bibs = bibs
    self.name = name


for infile in os.listdir(dir_path):
  print "Starting parsing file %s" % infile
  if infile.endswith(".bib"):
    print infile
    bibfiles = Bibfile(parser.parse_file(dir_path+infile),infile)