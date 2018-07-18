#!/usr/bin/python

#
# This scripts runs through the folder 'nime/web/2012' and renames the pdf documents to convention. 
# Scripts named 'XXX_Final_Manuscript.pdf' are renamed to 'nime2012_XXX'
#

import os

dir_path = "nime_archive/web/2012" 
#iterates through each file in path 2012
for file in os.listdir(dir_path):
    lfile = os.path.join(dir_path, file)
    if os.path.isfile(lfile):
        #extracts id_number from pdf file
        num = file.split('_')[0]
        #prepends correct number of zeros if name less than tre digits (treated as strings) e.g 2 becomes 002
        if len(num) == 2:
            num = "0%s" % num
        elif len(num) == 1:
            num = "00%s" % num
        
        #generates destination file
        destfile = dir_path+"/nime2012_%s.pdf" % num
        #renames
        os.rename(lfile,destfile)
        #prints notification
        print "File: %s \t renamed to: %s." % (lfile, destfile)

