FORMATS = bib csv yaml json
TYPES = papers music installations alt

RELEASE_FILES = $(foreach t,$(TYPES),$(foreach f,$(FORMATS),release/nime_$(t).$(f)))

# Each collated file is rebuilt when its proceedings files or the tool change.
PAPER_BIBS = $(wildcard paper_proceedings/nime*.bib)
MUSIC_BIBS = $(wildcard music_proceedings/nime*_music.bib)
INSTALLATION_BIBS = $(wildcard installation_proceedings/nime*_installations.bib)
ALT_BIBS = $(wildcard alt_proceedings/nime*_alt.bib)
TOOL = $(wildcard nime_bib/*.py)

.PHONY: all
all: $(RELEASE_FILES) release/index.html

release/nime_papers.%: $(PAPER_BIBS) $(TOOL)
	poetry run python nime_bib collate --type paper --format $*

release/nime_music.%: $(MUSIC_BIBS) $(TOOL)
	poetry run python nime_bib collate --type music --format $*

release/nime_installations.%: $(INSTALLATION_BIBS) $(TOOL)
	poetry run python nime_bib collate --type installation --format $*

release/nime_alt.%: $(ALT_BIBS) $(TOOL)
	poetry run python nime_bib collate --type alt --format $*

release/index.html: scripts/create_release_index.sh
	sh scripts/create_release_index.sh

.PHONY: clean
clean:
	rm -rf release
