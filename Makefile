.PHONY: scrape-all

# Scrape order matters: games + teams + players first, then stats that depend on them
scrape-all:
	python src/scraping/get_teams.py
	python src/scraping/get_games.py
	python src/scraping/get_players.py
	python src/scraping/get_playerStats.py
	python src/scraping/get_playerGameStats.py

.PHONY: compute-all

# standings must run before bracket (bracket reads standings.json)
# roster can run in parallel but make runs sequentially by default
compute-all:
	python src/compute_standings.py
	python src/compute_bracket.py
	python src/compute_roster.py

.PHONY: all

all: scrape-all compute-all

.PHONY: clean

clean:
	rm -rf src/data docs/data

.PHONY: serve

serve:
	python -m http.server 8000 --directory docs