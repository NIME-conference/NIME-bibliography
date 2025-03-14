BIBFILES = release/nime_installations.bib release/nime_music.bib release/nime_papers.bib
CSVFILES = release/nime_installations.csv release/nime_music.csv release/nime_papers.csv
YAMLFILES = release/nime_installations.yaml release/nime_music.yaml release/nime_papers.yaml
JSONFILES = release/nime_installations.json release/nime_music.json release/nime_papers.json

.PHONY: all
all: $(BIBFILES) $(CSVFILES) $(YAMLFILES) $(JSONFILES) release/index.html

release/nime_installations.bib:
	poetry run python nime_bib collate --type installations --format bib --id_order

release/nime_installations.csv:
	poetry run python nime_bib collate --type installations --format csv --id_order

release/nime_installations.yaml:
	poetry run python nime_bib collate --type installations --format yaml --id_order

release/nime_installations.json:
	poetry run python nime_bib collate --type installations --format json --id_order

release/nime_music.bib:
	poetry run python nime_bib collate --type music --format bib --id_order

release/nime_music.csv:
	poetry run python nime_bib collate --type music --format csv --id_order

release/nime_music.yaml:
	poetry run python nime_bib collate --type music --format yaml --id_order

release/nime_music.json:
	poetry run python nime_bib collate --type music --format json --id_order

release/nime_papers.bib:
	poetry run python nime_bib collate --type papers --format bib --id_order

release/nime_papers.csv:
	poetry run python nime_bib collate --type papers --format csv --id_order

release/nime_papers.yaml:
	poetry run python nime_bib collate --type papers --format yaml --id_order

release/nime_papers.json:
	poetry run python nime_bib collate --type papers --format json --id_order

release/index.html:
	sh scripts/create_release_index.sh

.PHONY: clean
clean: 
	rm release/*
