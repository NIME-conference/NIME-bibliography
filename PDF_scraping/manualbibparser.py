#!/usr/bin/python
#-*- coding: utf-8

import os, re, sys, traceback, time
import xml.etree.ElementTree as ET
from pybtex.database.input import bibtex

URL_PATTERN = re.compile('(nime\d{4}_\d{3}.pdf)',re.IGNORECASE)


dir_path = r"nime_archive/nime/bibtex/"
out_path = r"output_bibtex/"
result_path = 'result_cleaned.xml'
tree = ET.parse(result_path)
root = tree.getroot()

global exception_cnt
global texts_cnt
exception_cnt = 0
texts_cnt = 0

results = {}

for document  in root.iter('document'):
  name = document.find('name').text
  results[name] = {}
  if document.find('abstract') != None:
     results[name]['abstract'] = document.find('abstract').text
  if document.find('keywords') != None:
     results[name]['keywords'] = document.find('keywords').text


def seekread(): 
  for infile in os.listdir(dir_path):
      print "Starting parsing file %s" % infile
      if infile.endswith(".bib"):
        elements = {}
        doc = open(dir_path+infile).read()
        outfile = open(out_path+infile,"w")
        i = 0
        while i>-1:
          element = {}
          i = doc.find('{',i)
          nameend = i+1
          while not doc[nameend].isspace() and doc[nameend] != ',':
            nameend = nameend + 1
          entryname =  doc[i+1:nameend]
          j = readbraces(i+1,doc)
          while i >-1:
            i, key, val= readelement(i,doc)
            if i < 0:
              break
            element[key] = val
          '''
          k = readnontoken(i+1, doc)
          if doc[k].isalpha():
            i = k 
            k = readtoken(i,doc)
            print doc[i:k]
          else: 
            i = k
            k = readbraces(i+1, doc)
            print doc[i:k]
            '''
          #print "HER:",element
          
          try:
            ref = re.findall(URL_PATTERN, element["url"])[0]
            if 'keywords' in results[ref]:
              element['keywords'] =  results[ref]['keywords']
              
            if 'abstract' in results[ref]:
              element['abstract'] =  results[ref]['abstract']
          
          except (KeyError, IndexError) as e:
            #print "Error: " 
            print " "
          
          tempa = "@inproceedings{%s\n" % entryname
          outfile.write(tempa)
          for key, value in element.iteritems():
            temps = "%s = {%s}\n" % (key, value)
            outfile.write(temps)  
            #print element
          outfile.write('}\n')
          i = j
        outfile.close()


          
        
def readbraces(i, doc):
  inn = doc.find('{',i)
  ut = doc.find('}',i)
  while inn > -1 and inn < ut:
    i = readbraces(inn+1, doc)
    if i == -1:
      return -1
    inn = doc.find('{',i)
    ut = doc.find('}',i)
  if ut > -1:
    ut = ut + 1
  return ut

def readtoken(i, doc):
  while doc[i].isalnum():
    i = i + 1
    if i >= len(doc):
      return -1
  return i
  
def readnontoken(i, doc):
  while not doc[i].isalpha() and not doc[i]=='{':
    i = i + 1
    if i >= len(doc):
      return -1
  return i
  
def readelement(i,doc):
  j = doc.find('=',i)
  i = doc.find('}',i)
  if i < j: 
    return -1, "", ""
  k = doc.find('{',j)
  m = readbraces(k+1,doc)
  
  while not doc[j].isalnum():
    j = j - 1
  l = j+1
  while doc[j].isalnum():
    j = j - 1
  return m, doc[j+1:l], doc[k+1:m-1] 
      
seekread()