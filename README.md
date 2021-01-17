# Opferberatung Rheinland Scraper

Scraping right-wing incidents in North Rhine-Westphalia (_Nordrhein-Westfalen_), Germany as monitored by the NGO [Opferberatung Rheinland](https://www.opferberatung-rheinland.de).

-   Website: <https://www.opferberatung-rheinland.de/chronik-der-gewalt>
-   Data: <https://morph.io/rechtegewalt/opferberatung-rheinland-scraper>

## Usage

For local development:

-   Install [poetry](https://python-poetry.org/)
-   `poetry install`
-   `poetry run python scraper.py`

For Morph:

-   `poetry export -f requirements.txt --output requirements.txt`
-   commit the `requirements.txt`
-   modify `runtime.txt`

## Morph

This is scraper runs on [morph.io](https://morph.io). To get started [see the documentation](https://morph.io/documentation).

## License

MIT
