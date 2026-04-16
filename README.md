# ufa-data-analytics

Just playing around with ideas right now :)

View here - [https://seeilogiic.github.io/ufa-data-analytics/](https://seeilogiic.github.io/ufa-data-analytics/)

## Running locally

### Set up venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Download fresh data

```bash
make scrape-all
```

### Compute cleaned data

```bash
make compute-all
```

### Run local dev

```bash
make serve
```
