.PHONY: scrape-all

scrape-all:
	python src/scraping/get_teams.py
	python src/scraping/get_games.py
	python src/scraping/get_players.py
	python src/scraping/get_playerStats.py
	python src/scraping/get_playerGameStats.py
	python src/scraping/get_gameEvents.py

.PHONY: compute-all

compute-all:
	python src/compute_standings.py
	python src/compute_bracket.py

.PHONY: serve

serve:
	python -m http.server 8000 --directory docs