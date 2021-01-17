import re
from typing import SupportsRound

import dataset
import get_retries
from bs4 import BeautifulSoup
from dateparser import parse

from hashlib import md5

from tqdm import tqdm

db = dataset.connect("sqlite:///data.sqlite")

tab_incidents = db["incidents"]
tab_sources = db["sources"]
tab_chronicles = db["chronicles"]


tab_chronicles.upsert(
    {
        "iso3166_1": "DE",
        "iso3166_2": "DE-NW",
        "chronicler_name": "Opferberatung Rheinland",
        "chronicler_description": "Die Opferberatung Rheinland (OBR) hat im Juli 2012 ihre Beratungsarbeit aufgenommen.",
        "chronicler_url": "https://www.opferberatung-rheinland.de",
        "chronicle_source": "https://www.opferberatung-rheinland.de/chronik-der-gewalt",
    },
    ["chronicler_name"],
)


BASE_URL = "https://www.opferberatung-rheinland.de/chronik-der-gewalt/chronik-"


def fix_date_typo_missing(x):
    """"""
    if not ":" in x:
        x = re.sub(r"(\d{1,2}\.\d{1,2}\.\d\d) ", r"\1: ", x)
    return x


def ends_with_date_like(x):
    regex = re.compile(r".*\d{1,2}\.\d{1,2}\.\d\d")
    return re.match(regex, x.strip()) is not None


def fetch(url):
    res = get_retries.get(url, verbose=True, max_backoff=128)
    if res is None:
        return None
    html_content = res.text
    soup = BeautifulSoup(html_content, "lxml")
    return soup


# https://stackoverflow.com/a/7160778/4028896
def is_url(s):
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(regex, s) is not None


def process_report(report, url):
    h_a = report.select_one(".header a")
    rg_id = url = "https://www.opferberatung-rheinland.de" + h_a.get("href")
    # print(h_a.get_text())
    date, city = fix_date_typo_missing(h_a.get_text()).split(":")
    date = parse(date, languages=["de"])
    city = city.strip()

    texts = report.select(".teaser-text p")
    description = None

    texts = [t for t in texts if t.get_text().strip() != ""]

    if len(texts) == 0:
        # invalid data, no description
        return
    elif len(texts) == 1:
        texts = fetch(url).select("#maincontent .article .news-text-wrap p")
        texts = [t for t in texts if t.get_text().strip() != ""]

    sources = []
    if len(texts) == 2:
        description = texts[0].get_text(separator="\n").strip()
        # print(texts)

        source_text = texts[1].get_text()
        source_class = texts[1].get("class")
        source_style = texts[1].get("style")
        if not (source_class or source_style) and not ends_with_date_like(source_text):
            raise ValueError("X")
        for s in source_text.split(","):
            sources.append({"name": s.strip(), "rg_id": rg_id})
    else:
        raise ValueError("X")

    data = dict(
        chronicler_name="Opferberatung Rheinland",
        description=description,
        city=city,
        date=date,
        rg_id=rg_id,
        url=url,
    )

    tab_incidents.upsert(data, ["rg_id"])

    for s in sources:
        tab_sources.upsert(s, ["rg_id", "name", "url"])


def process_page(page, url):
    for row in page.select("#maincontent .news-list-view .article"):
        process_report(row, url)

    # next_link = page.select_one("li.pager-next a")

    # if next_link is None:
    #     return None

    # return "https://response-hessen.de" + next_link.get("href")


i = 2012

while True:
    url = BASE_URL + str(i)
    print(url)
    soup = fetch(url)
    if soup is None:
        break
    process_page(soup, url)
    i += 1

