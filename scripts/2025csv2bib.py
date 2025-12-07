import re
import csv
import shutil
from pypdf import PdfReader


# Move PDF files to proceedings format
PAPERS_IN_DIR = "NIME2025-camera-ready"
#PAPERS_OUT_DIR = "NIME2025-paper-proceedings"
PAPERS_OUT_DIR = "NIME2025-music-proceedings"

def convert_csv_to_bibtex(csv_file, bibtex_file, copy_files = False):
    """Convert a CSV file to BibTeX format"""
    with open(csv_file, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        prev_last_page = 0 # for tracking page numbers through the proceedings

        with open(bibtex_file, "w", encoding="utf-8") as bibtexfile:
            for row in reader:
                
                # read data out of the CSV
                cmt_id = row["cmtID"]
                number = row["number"]
                #key = f"nime2025_{number}"
                key = f"nime2025_music_{number}"
                author = row["proc-authors"]
                author = re.sub("([\(]).*?([\)])", "\g<1>\g<2>", author)
                author = re.sub("[()*]", '', author)
                author = re.sub(r";", " and", author) # the replaced string can be "and" or " and" (depends on the starting csv)
                author = author.rstrip()
                title = row["title"]
                booktitle = "Proceedings of the International Conference on New Interfaces for Musical Expression"
                #editor = "Doga Cavdir and Florent Berthaut" 
                editor = "Sophie Rose and Jos Mulder and Nicole Carroll"
                year = "2025"
                month = "June"
                address = "Canberra, Australia"
                issn = "2220-4806"
                url = f"http://nime.org/proceedings/{year}/{key}.pdf"
                track = row["track"]
                note = row["note"] #form music only (“Live Performance”, “Remote Performance”, or “Installation”)
                video = row["video"]
                abstract = row["abstract"]
                supp1 = row["supp1"]
                supp2 = row["supp2"]
                supp3 = row["supp3"]
                if abstract.find('-\n') > -1:
                    abstract = re.sub('-\n', '', abstract)
                    abstract = re.sub('\n', ' ', abstract)
                else:
                    abstract = re.sub('\n', '', abstract)

                # calculate page number
                src = f"{PAPERS_IN_DIR}/{cmt_id}.pdf"
                dst = f"{PAPERS_OUT_DIR}/{key}.pdf"
                src_paper_reader = PdfReader(src)
                num_pages = len(src_paper_reader.pages)
                print(f"Num pages: {num_pages}")
                # Page counting logic.
                first_page = prev_last_page + 1
                last_page = prev_last_page + num_pages
                prev_last_page = last_page

                # Construct BibTeX entry
                bibtex_entry = f"@inproceedings{{{key},\n" \
                               f"  author = {{{author}}},\n" \
                               f"  title = {{{title}}},\n" \
                               f"  pages = {{{first_page}--{last_page}}},\n" \
                               f"  numpages = {{{num_pages}}},\n" \
                               f"  booktitle = {{{booktitle}}},\n" \
                               f"  editor = {{{editor}}},\n" \
                               f"  year = {{{year}}},\n" \
                               f"  month = {{{month}}},\n" \
                               f"  address = {{{address}}},\n" \
                               f"  issn = {{{issn}}},\n" \
                               f"  url = {{{url}}},\n"

                # Add supplementary files only if not empty
                if supp1:
                    suppurl = f"http://nime.org/proceedings/{year}/{key}_file01.{supp1}"
                    bibtex_entry += f"  urlsuppl1 = {{{suppurl}}},\n"

                if supp2:
                    suppurl = f"http://nime.org/proceedings/{year}/{key}_file02.{supp2}"
                    bibtex_entry += f"  urlsuppl2 = {{{suppurl}}},\n"

                if supp3:
                    suppurl = f"http://nime.org/proceedings/{year}/{key}_file03.{supp3}"
                    bibtex_entry += f"  urlsuppl3 = {{{suppurl}}},\n"
                
                # Add presentation-video only if video is not empty
                if video.strip():
                    bibtex_entry += f"  presentation-video = {{{video}}},\n"

                bibtex_entry += f"  articleno = {{{number}}},\n" \
                                f"  track = {{{track}}},\n" \
                                f"  note = {{{note}}},\n" \
                                f"  abstract = {{{abstract}}}\n" \
                                f"}}\n\n"

                    
                bibtexfile.write(bibtex_entry)

                if copy_files:
                    print(f"Copying: {src} to {dst}")
                    shutil.copyfile(src, dst)
                    if supp1:
                        src = f"{PAPERS_IN_DIR}/{cmt_id}.{supp1}"
                        dst = f"{PAPERS_OUT_DIR}/{key}_file01.{supp1}"
                        print(f"Copying: {src} to {dst}")
                        shutil.copyfile(src, dst)
                    if supp2:
                        src = f"{PAPERS_IN_DIR}/{cmt_id}.{supp2}"
                        dst = f"{PAPERS_OUT_DIR}/{key}_file02.{supp2}"
                        print(f"Copying: {src} to {dst}")
                        shutil.copyfile(src, dst)
                    if supp3:
                        src = f"{PAPERS_IN_DIR}/{cmt_id}.{supp3}"
                        dst = f"{PAPERS_OUT_DIR}/{key}_file03.{supp3}"
                        print(f"Copying: {src} to {dst}")
                        shutil.copyfile(src, dst)

#Do the Conversion
#convert_csv_to_bibtex("./NIME2025.csv", "nime2025_papers.bib", copy_files=True)
convert_csv_to_bibtex("./NIME2025-Music.csv", "nime2025_music.bib", copy_files=True)

