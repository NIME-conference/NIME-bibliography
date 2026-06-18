BIBFILES = release/nime_alt.bib release/nime_installations.bib release/nime_music.bib release/nime_papers.bib
CSVFILES = release/nime_alt.csv release/nime_installations.csv release/nime_music.csv release/nime_papers.csv
YAMLFILES = release/nime_alt.yaml release/nime_installations.yaml release/nime_music.yaml release/nime_papers.yaml
JSONFILES = release/nime_alt.json release/nime_installations.json release/nime_music.json release/nime_papers.json

.PHONY: all
all: $(BIBFILES) $(CSVFILES) $(YAMLFILES) $(JSONFILES) release/index.html

release/nime_alt.bib:
	poetry run python nime_bib collate --type alt --format bib --id_order

release/nime_alt.csv:
	poetry run python nime_bib collate --type alt --format csv --id_order

release/nime_alt.yaml:
	poetry run python nime_bib collate --type alt --format yaml --id_order

release/nime_alt.json:
	poetry run python nime_bib collate --type alt --format json --id_order

release/nime_installations.bib:
	poetry run python nime_bib collate --type installation --format bib --id_order

release/nime_installations.csv:
	poetry run python nime_bib collate --type installation --format csv --id_order

release/nime_installations.yaml:
	poetry run python nime_bib collate --type installation --format yaml --id_order

release/nime_installations.json:
	poetry run python nime_bib collate --type installation --format json --id_order

release/nime_music.bib:
	poetry run python nime_bib collate --type music --format bib --id_order

release/nime_music.csv:
	poetry run python nime_bib collate --type music --format csv --id_order

release/nime_music.yaml:
	poetry run python nime_bib collate --type music --format yaml --id_order

release/nime_music.json:
	poetry run python nime_bib collate --type music --format json --id_order

release/nime_papers.bib:
	poetry run python nime_bib collate --type paper --format bib --id_order

release/nime_papers.csv:
	poetry run python nime_bib collate --type paper --format csv --id_order

release/nime_papers.yaml:
	poetry run python nime_bib collate --type paper --format yaml --id_order

release/nime_papers.json:
	poetry run python nime_bib collate --type paper --format json --id_order

release/index.html:
	sh scripts/create_release_index.sh

.PHONY: clean
clean: 
	rm release/*
