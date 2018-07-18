#!/usr/bin/python
#-*- coding: utf-8

import xml.etree.ElementTree as ET

abstr_counter = 0
keywrd_counter = 0

tree = ET.parse('result.xml')
root = tree.getroot()
documents =  root.findall('document')
print len(documents)

for el in documents: 
  abstr = el.find('abstract')
  keywrd = el.find('keywords')
  
  if abstr != None:
    print abstr.text 
    abstr_counter += 1
  if keywrd !=  None:
    print keywrd.text
    keywrd_counter += 1
    

print "abstract counter: %d" % abstr_counter
print "keywords counter: %d" % keywrd_counter