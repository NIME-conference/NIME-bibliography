.PHONY: all
all: release/nime_installations.bib release/nime_music.bib release/nime_papers.bib release/index.html

release/nime_installations.bib:
	poetry run python nime_bib collate --type installations

release/nime_music.bib:
	poetry run python nime_bib collate --type music

release/nime_papers.bib:
	poetry run python nime_bib collate --type papers

release/index.html:
	sh scripts/create_release_index.sh

