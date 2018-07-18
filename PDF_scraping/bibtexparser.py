#!/usr/bin/python
#-*- coding: utf-8

import os, re, sys, traceback
import xml.etree.ElementTree as ET
from pybtex.database.input import bibtex

URL_PATTERN = re.compile('nime\d{4}_\d{3}.pdf',re.IGNORECASE)

dir_path = r"nime_archive/nime/bibtex/"
result_path = 'result_cleaned.xml'
tree = ET.parse(result_path)
root = tree.getroot()
global exception_cnt
global texts_cnt
exception_cnt = 0
texts_cnt = 0


## Reading the document structure

results = {}

for document  in root.iter('document'):
  name = document.find('name').text
  results[name] = {}
  print document.find('name').text
  if document.find('abstract') != None:
     results[name]['abstract'] = document.find('abstract').text
  if document.find('keywords') != None:
     results[name]['keywords'] = document.find('keywords').text


num_texts = 0


#Open and parse the XML structure created from the results of the extraction processs

class Bibfile:
  def __init__(self,bibs,name):
    global exception_cnt
    global texts_cnt
    self.bibs = bibs
    self.name = name
    num_text = 0
    self.bibs.entries
    print "\n\n"
    for a in self.bibs.entries.keys():
       texts_cnt += 1
       num_text += 1
       try:
         print bibs.entries[a].fields['url']
       except KeyError as e:
         print "Could not find URL. Hint, it's in year: %s " % name
         continue
         
       try:

         # Do a search for file. 
         res = re.findall(URL_PATTERN,bibs.entries[a].fields['url'])

         if res > 0:
           if results[res[0]]['abstract']:
             #abs_holder = {'abstract': }
             self.bibs.entries[a]['abstract'] = results[res[0]]['abstract']
           else:
             print "Error: no abstract key in %s" % res
           #bibs.entries[a]['abstract'] = 
           if results[res[0]]['abstract']:
               #key_holder = {'keywords':results[res[0]]['keywords']}
               self.bibs.entries[a]['abstract'] = results[res[0]]['keywords']
           else:
             print "Error: no keywords key in %s" % res
           #print res[0]
         # Search up id in the XML with results.
           
             
       except (KeyError, ValueError, IndexError), e:
         exception_cnt += 1
         print traceback.format_exc()
         print "Error: %s for file " % (e)
         if res !=  None:
           print "for file: %s" % res



bibfiles = []
parser = bibtex.Parser()


for infile in os.listdir(dir_path):
    print "Starting parsing file %s" % infile
    if infile.endswith(".bib"):
      print infile
      bibfiles = Bibfile(parser.parse_file(dir_path+infile),infile)
      
print "program terminated sucessfully... at least it came to the last instruction. With %s exception and %s texts" % (str(exception_cnt), str(texts_cnt))
      
