BIBFILES = release/nime_installations.bib release/nime_music.bib release/nime_papers.bib
CSVFILES = release/nime_installations.csv release/nime_music.csv release/nime_papers.csv
YAMLFILES = release/nime_installations.yaml release/nime_music.yaml release/nime_papers.yaml
JSONFILE = release/nime_installations.json release/nime_music.json release/nime_papers.json

.PHONY: all
all: $(BIBFILES) $(CSVFILES) $(YAMLFILES) $(JSONFILES) release/index.html

release/nime_installations.bib:
	poetry run python nime_bib collate --type installations --format bib

release/nime_installations.csv:
	poetry run python nime_bib collate --type installations --format csv

release/nime_installations.yaml:
	poetry run python nime_bib collate --type installations --format yaml

release/nime_installations.json:
	poetry run python nime_bib collate --type installations --format json

release/nime_music.bib:
	poetry run python nime_bib collate --type music --format bib

release/nime_music.csv:
	poetry run python nime_bib collate --type music --format csv

release/nime_music.yaml:
	poetry run python nime_bib collate --type music --format yaml

release/nime_music.json:
	poetry run python nime_bib collate --type music --format json

release/nime_papers.bib:
	poetry run python nime_bib collate --type papers --format bib

release/nime_papers.csv:
	poetry run python nime_bib collate --type papers --format csv

release/nime_papers.yaml:
	poetry run python nime_bib collate --type papers --format yaml

release/nime_papers.json:
	poetry run python nime_bib collate --type papers --format json

release/index.html:
	sh scripts/create_release_index.sh

.PHONY: clean
clean: 
	rm release/*
