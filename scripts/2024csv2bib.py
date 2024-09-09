import re
import csv
import shutil
from pypdf import PdfReader


# Move PDF files to proceedings format
PAPERS_IN_DIR = "NIME2024-camera-ready"
PAPERS_OUT_DIR = "NIME2024-paper-proceedings"

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
                key = f"nime2024_{number}"
                author = row["proc-authors"]
                author = re.sub("([\(]).*?([\)])", "\g<1>\g<2>", author)
                author = re.sub("[()*]", '', author)
                author = re.sub(r";", "and", author)
                author = author.rstrip()
                title = row["title"]
                booktitle = "Proceedings of the International Conference on New Interfaces for Musical Expression"
                editor = "Astrid Bin and Courtney Nicole Reed"
                year = "2024"
                month = "September"
                address = "Utrecht, Netherlands"
                issn = "2220-4806"
                url = f"http://nime.org/proceedings/{year}/{key}.pdf"
                track = row["track"]
                video = row["video"]
                abstract = row["abstract"]
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

                bibtex_entry = f"@article{{{key},\n" \
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
                               f"  url = {{{url}}},\n" \
                               f"  presentation-video = {{{video}}},\n" \
                               f"  articleno = {{{number}}},\n" \
                               f"  track = {{{track}}},\n" \
                               f"  abstract = {{{abstract}}}\n" \
                               f"}}\n\n"
                bibtexfile.write(bibtex_entry)

                if copy_files:
                    print(f"Copying: {src} to {dst}.")
                    shutil.copyfile(src, dst)

# Example usage
PAPERS_CSV_FILE = "./NIME2024.csv"

# Do the Conversion
convert_csv_to_bibtex(PAPERS_CSV_FILE, "nime2024_papers.bib", copy_files=True)



# f"@inproceedings{article_id,
#   urlsuppl1 = {},
#   urlsuppl2 = {},
#   urlsuppl3 = {},
#   pdf = {},
# }
