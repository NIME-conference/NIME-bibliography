#!/usr/bin/python
#-*- coding: utf-8


#
# This script runs through the pdf files in the nime2012 folder and tries to extact text from the pdf files. Text is written to screen.
# Should implement a limitation on how much of the files which are printed. Should also look for formatting. 
#
# Alternative python pdf libraries: pyPdf, PDFMiner
# Tip from stackoverflow: https://code.google.com/p/pdfssa4met/

import os
import re
from pyPdf import PdfFileReader
import subprocess

abstract_word = "abstract"
introduction_word = {"intro", "introduction"}
SEARCHSTRING = re.compile('(abstract)(.*)(keywords)(.*)(INTRODUCTION)', flags=re.MULTILINE | re.IGNORECASE)

dir_path = "nime_archive/web/"
found = {}
found_nothing = {}



class PdfDoc:
	#Instanciates the PdfDoc object. Reads the file and sets various variables
	def __init__(self, pdf):
		self.pdf = pdf
        try:
            meta = pdf.getDocumentInfo()
			producer = meta['/Producer']
            print "filename: %s \t \t producer = %s " % (infile, meta['/Producer'])
        except Exception as e:
            print "error extracting DocumentInfo from file:%s, %s" % (workfile ,e)
	
	def search():
		if found:
			return True
		else
			return False
		
	
	


for folder in os.listdir(dir_path):
    found[folder] = 0
    found_nothing[folder] = 0
    if os.path.isdir(dir_path+folder) == True:
        for infile in os.listdir(dir_path+folder):
            #print infile
            if infile.endswith(".pdf"):
                workfile = dir_path + folder + "/"+ infile
				try:
		            input1 = PdfFileReader(file(workfile, "rb"))
		        except Exception as e:
		            print "Could not open file: %s, %s" % (workfile,e)
		            break
                
                try:
                    pagenum = (input1.getNumPages())
                    for i in range(0,pagenum):
                        try:
                            #print "!!--- PAGE START: %i ---!!" % i
                            fp = input1.getPage(i)
                            text = fp.extractText()
                            
                            splits = re.findall(SEARCHSTRING, text)
                            if len(splits) > 0:
                               # print "Found %s " % splits
                               print "Found %s" % infile
                               found[folder] = found[folder] + 1
                               print found[folder]
                            else:
                                if i == 0:
                                    print "Found nothing: %s" % infile
                                    found_nothing[folder] = found_nothing[folder] + 1
                                    print found_nothing[folder]
                        except Exception as e:
                            print "error extracting text: %s \t as %s" %(workfile ,e)    
                except Exception as e:
                       print "Error extracting pagenumber from pdf file: %s with error: %s" % (workfile, e)

for folder in os.listdir(dir_path):
    print "Number completed: %i, not completed: %i, percentage extracted: %i for %s" % (int(found[folder]), int(found_nothing[folder]), int(found[folder])/(int(found[folder])+int(found_nothing[folder]), folder))
    
        
