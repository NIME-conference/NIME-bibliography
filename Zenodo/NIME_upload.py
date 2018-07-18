########################################################
'''
Written by Benedikte Wallace, 2018.


NIME_upload.py:

This script reads .bib files in NIME archive and creates a deposition record 
on the Zenodo website. The metadata from the .bib entries are tied to the 
article (.pdf file) and are publishedd to Zenodo resulting in the creation 
of a DOI. When this script is used to upload a new batch of papers the DOI
and file name of each paper are added to the text file NIME_dois.txt. 

Run:

Place script in the directory which contains the .bib file and all .pdf's. 
Then run using 'python NIME_upload.py'


Additional files:

If a resource contains an additional file that should be uploaded together with the paper
this additional file should have the same file name with an additional file01 appended to the end.
Zenodo displays the files alphabetically.
pr. today this script only allows for adding one additional file pr. resource.

The .bib file:

Special charachters in the .bib file should be written in LaTeX code.


'''
########################################################


import json
import requests
import os
import sys
import codecs
import latexcodec
import re
import datetime

from pybtex.database.input import bibtex



# Bibtex parser
parser = bibtex.Parser()

# Bibtex file to be used for the upload
bibfile = 'REPLACE_WITH_BIBFILENAME.bib'

# Time stamp used when writing to NIME_dois.txt
now = datetime.datetime.now()

# New dois and file names are appended to the text file NIME_dois.txt 
doi_file = open("NIME_dois.txt", "a+")
# Add date and time for this upload
doi_file.write(now.strftime("Uploaded %Y-%m-%d %H:%M \n"))


# Tokens, replace with public and sandbox tokens from Zenodo: 
PUBLIC_TOKEN = ''
SANDBOX_TOKEN = ''

# Token in use
TOKEN = SANDBOX_TOKEN

# TODO: once you are sure about what you are doing, remove the "sandbox." part
BASE_URL = 'https://sandbox.zenodo.org' 


def upload(metadata, pdf_path):
	''' 
	upload(metadata, pdf_path):
	- connects to zenodo REST API, 
	- creates a new record, 
	- enters metadata, 
	- uploads the .pdf and 
	- publishes it
	
	'''
	print("\n ############## START UPLOAD: NEW FILE ############## \n")

	url = BASE_URL+'/api/deposit/depositions'
	access_depositions = requests.get(url, params={'access_token': TOKEN})
	print("Access depositions: ", access_depositions.status_code)
	# Create new paper submission - add parsed metadat
	headers = {"Content-Type": "application/json"}
	new_deposition = requests.post(url,params={'access_token': TOKEN}, json=metadata, headers=headers)


	# If creation of new deposition is unsuccessfull, abort
	if new_deposition.status_code > 210:
		print("Error happened during submission {}, status code: ".format(pdf_path) + str(new_deposition.status_code))
		print(new_deposition.json())
		return

	submission_id = json.loads(new_deposition.text)["id"]

	# Upload the pdf file
	url = BASE_URL+"/api/deposit/depositions/{id}/files?access_token={token}".format(id=str(submission_id), token=TOKEN)
	upload_metadata = {'filename': 'paper.pdf'}
	files = {'file': open(pdf_path, 'rb')}


	# atempt to add files to record
	add_file = requests.post(url, data=upload_metadata, files=files)

	# If upload of file is unsuccessfull, abort
	if add_file.status_code > 210:
		print("Error happened during file upload, status code: " + str(add_file.status_code))
		print(add_file.json())
		return
	
	# Checking to see if there exist additional files for this resource. NB! must have name 'xxxxxfile01.pdf'. 
	pdf_fname = pdf_path[:-4]
	extra1 = 'file01.pdf'
	try:
		extra_file = open(pdf_fname+extra1, 'rb')
		files = {'file': extra_file}
		upload_metadata = {'filename': 'paper.pdf'}
		# atempt to add files to record
		add_file = requests.post(url, data=upload_metadata, files=files)

		# If upload of file is unsuccessfull, abort
		if add_file.status_code > 210:
			print("Error happened during file upload, status code: " + str(add_file.status_code))
			print(add_file.json())
			return

	except FileNotFoundError:
		pass	
	
	
	print("{file} submitted with submission ID = {id} (DOI: 10.5281/zenodo.{id})".format(file=pdf_path,id=submission_id))    
	

	# publish the new deposition
	publish_record = requests.post(BASE_URL+'/api/deposit/depositions/%s/actions/publish' % submission_id,params={'access_token': TOKEN})

	# If publish unsuccessfull, abort
	if publish_record.status_code > 210:
		print("Error happened during file upload, status code: " + str(publish_record.status_code))
		print(publish_record.json())
		return


	print("{file} PUBLISHED with submission ID = {id} (DOI: 10.5281/zenodo.{id})".format(file=pdf_path,id=submission_id))
	doi_file.write('Filename: {} DOI: 10.5281/zenodo.{}\n'.format(*[pdf_path, submission_id]))



def format_metadata(bibfilename=None):
	''' 
	format_metadata(bibfilename):
	- formats contents of entries in the .bib file referenced by bibfilename
	- for each entry, metadata is formatted and the upload function 
	above is called in order to publish record
	'''

	if bibfilename == None:
		print("Missing .bib file")
		return


	bibdata = parser.parse_file(bibfilename)

	title = 'title'
	abstract = 'abstract'
	address = 'adress'
	creators = 'creators'
	pubdate = '20XX-06-01'
	pages = 'x-x'
	conf_url = ''
	pdf_name = ''
	creators = []


	#loop through the individual entries
	for bib_id in bibdata.entries:
		title = 'title'
		abstract = 'abstract'
		address = 'adress'
		creators = 'creators'
		pubdate = '20XX-06-01'
		pages = 'x-x'
		conf_url = ''
		pdf_name = ''
		creators = []

		b = bibdata.entries[bib_id].fields
		try:
			conf_url = b['Url']
			pdf_name = conf_url.rsplit('/', 1)[-1]

			title = b['Title']
			for author in bibdata.entries[bib_id].persons["Author"]:    
				names = {}
				tex = bytes(str(author),"utf-8")
				decoded_tex = tex.decode("latex","ignore")
				cleaned_tex = decoded_tex.replace("}","")
				cleaned_tex = cleaned_tex.replace("{","")
				cleaned_tex = cleaned_tex.replace("\\\"","")
				names['name'] = cleaned_tex 
				
				creators.append(names)

			yr_seg = conf_url.rsplit('/', 1)[-2]
			yr = yr_seg.rsplit('/', 1)[-1]
			pubdate = yr + pubdate[4:]

			address = b.get('Address', 'Address')
			pages = b.get('Pages', 'x-x')
			abstract = b.get('Abstract', '---') # if no abstract is found, --- will be used as default

			data = {
			'metadata': {
			'title': title, 
			'upload_type': 'publication', 
			'publication_type' : 'conferencepaper',
			'description': abstract,
			'conference_place': address,
			'conference_title':'International Conference on New Interfaces for Musical Expression',
			'publication_date' : pubdate,
			'partof_pages' : pages,
			'partof_title' : 'Proceedings of the International Conference on New Interfaces for Musical Expression',
			'creators': creators,
			'communities': [{'identifier': 'nime_conference'}] # adds the record to the zenodo NIME community
			}}

			upload(data,pdf_name)

		except(KeyError): # TODO Write failed bib ID's to a text file?
			print("KeyError! Entry did not contain fields needed, continuing to next id - failed bib id: ", bib_id)
			continue


	



# Begin upload by formatting metadata. This function calls the upload function for each entry in the .bib file
format_metadata(bibfile)

# Closes the text file after all files are uploaded.
doi_file.close()


