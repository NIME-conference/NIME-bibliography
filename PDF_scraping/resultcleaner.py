#!/usr/bin/python
#-*- coding: utf-8

import os, re, sys
import xml.etree.ElementTree as ET

def clean_abstract(abst):
  abst = abst.lstrip(' ')
  abst = abst.replace('\n\n','\n')
  abst = abst.replace('  ',' ')
  abst = abst.replace('-\n','')
  abst = abst.replace('- \n','')
  abst = abst.replace('\n','')
  abst = abst.replace('  ',' ')
  
  return abst
  
def clean_keywords(keywrd):
  keywrd = keywrd.lstrip(' ')
  keywrd = keywrd.replace('\n','')
  keywrd = keywrd.replace('  ',' ')
  return keywrd

#
# MAIN PROGRAM STARTS RUNNING
#


result_path = 'result.xml'
tree = ET.parse(result_path)
root = tree.getroot()

for document in root.iter('document'):
  print document.find('name').text
  if document.find('abstract') != None:
    # print clean_abstract(document.find('abstract').text)
     document.find('abstract').text = clean_abstract(document.find('abstract').text)
     
  if document.find('keywords') != None:
    # print clean_keywords(document.find('keywords').text)
     document.find('keywords').text = clean_keywords(document.find('keywords').text)
     

for document in root.iter('document'):
   print document.find('name').text
   if document.find('abstract') != None:
      print document.find('abstract').text

   if document.find('keywords') != None:
      print document.find('keywords').text
      

tree.write('result_cleaned.xml')


sys.exit(0)

