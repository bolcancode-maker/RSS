import datetime
import os
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

HEADERS = {"User-Agent": "Mozilla/5.0"}
ALLOWED_HOSTS = {"www.vesti.bg", "vesti.bg"}

CATEGORIES = [
    ("posledni-novini.xml", "Vesti.bg - Последни новини", "https://www.vesti.bg/posledni-novini"),
    ("avtomobili.xml", "Vesti.bg - Автомобили", "https://www.vesti.bg/avtomobili"),
    ("tehnologii.xml", "Vesti.bg - Технологии", "https://www.vesti.bg/tehnologii"),
    ("lyubopitno.xml", "Vesti.bg - Любопитно", "https://www.vesti.bg/lyubopitno"),
]

def norm(text: str) -> str:
    return " ".join((text or "").split()).strip()

def is_good_title(title: str) -> bool:
    if not title:
        return False
    if len(title) < 8:
        return False
    # често “Преди 3 минути”, “Преди 1 час” и т.н.
    if re.match(r"^Преди\s+\d+\s+(минути|минута|час|часа|дни|ден)$", title):
        return False
    return True

def is_internal_article_url(base_url: str, href: str):
    if not href:
        return None
    if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
        return None

    u = urljoin(base_url, href)
    p = urlparse(u)

    if p.scheme not in ("http", "https"):
        return None
    if p.netloc not in ALLOWED_HOSTS:
        return None
    if p.fragment:
        return None

    # режем очевидно “не-статии”
    bad_prefixes = ("/search", "/tags", "/tag", "/category", "/authors", "/author", "/contact", "/privacy", "/terms")
    if any(p.path.startswith(x) for x in bad_prefixes):
        return None

    # статията обикновено има поне 2 сегмента в пътя
    if len([x for x in p.path.split("/") if x]) < 2:
        return None

    return u

def create_feed(out_file: str, feed_title: str, list_url: str, max_items: int = 30):
    os.makedirs("feeds", exist_ok=True)
    filepath = os.path.join("feeds", out_file)

    fg = FeedGenerator()
    fg.id(list_url)
    fg.title(feed_title)
    fg.link(href=list_url, rel="alternate")
    fg.description(f"Автоматичен фийд от {list_url}")
    fg.language("bg")

    try:
        r = requests.get(list_url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        items = []
        seen = set()

        for a in soup.find_all("a", href=True):
            title = norm(a.get_text(" ", strip=True))
            if not is_good_title(title):
                continue

            link = is_internal_article_url(list_url, a["href"])
            if not link or link in seen:
                continue

            seen.add(link)
            items.append((title, link))
            if len(items) >= max_items:
                break

        now = datetime.datetime.now(datetime.timezone.utc)
        for title, link in items:
            fe = fg.add_entry()
            fe.id(link)
            fe.title(title)
            fe.link(href=link)
            fe.pubDate(now)

        fg.rss_file(filepath)
        print(f"✅ {filepath} (items: {len(items)})")

    except Exception as e:
        fg.description(f"Грешка при извличане: {e}")
        fg.rss_file(filepath)
        print(f"⚠️ Празен фийд: {filepath} (error: {e})")

if __name__ == "__main__":
    for out_file, title, url in CATEGORIES:
        create_feed(out_file, title, url, max_items=30)
