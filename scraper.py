import datetime
import os
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator


DNES_LAST_ARTICLES_URL = "https://www.dnes.bg/last-articles"
HEADERS = {"User-Agent": "Mozilla/5.0"}
ALLOWED_HOSTS = {"www.dnes.bg", "dnes.bg"}


def norm(text):
    return " ".join((text or "").split()).strip()


def is_internal_article_url(base_url, href):
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

    bad_prefixes = (
        "/search",
        "/tags",
        "/tag",
        "/category",
        "/authors",
        "/author",
        "/contact",
        "/privacy",
        "/terms",
        "/about",
    )
    if any(p.path.startswith(x) for x in bad_prefixes):
        return None

    if len([x for x in p.path.split("/") if x]) < 2:
        return None

    return u


def create_dnes_feed(out_file="dnes.xml", max_items=20):
    os.makedirs("feeds", exist_ok=True)
    filepath = os.path.join("feeds", out_file)

    fg = FeedGenerator()
    fg.id(DNES_LAST_ARTICLES_URL)
    fg.title("Новини от Dnes.bg (последни статии)")
    fg.link(href=DNES_LAST_ARTICLES_URL, rel="alternate")
    fg.description("Автоматичен фийд от /last-articles на Dnes.bg")
    fg.language("bg")

    try:
        r = requests.get(DNES_LAST_ARTICLES_URL, headers=HEADERS, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        items = []
        seen_links = set()

        for a in soup.find_all("a", href=True):
            title = norm(a.get_text(" ", strip=True))
            if len(title) < 8:
                continue

            link = is_internal_article_url(DNES_LAST_ARTICLES_URL, a["href"])
            if not link or link in seen_links:
                continue

            seen_links.add(link)
            items.append((title, link))

            if len(items) >= max_items:
                break

        for title, link in items:
            fe = fg.add_entry()
            fe.id(link)
            fe.title(title)
            fe.link(href=link)
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        fg.rss_file(filepath)
        print("✅ Успех: {} (items: {})".format(filepath, len(items)))

    except Exception as e:
        fg.description("Грешка при извличане: {}".format(e))
        fg.rss_file(filepath)
        print("⚠️ Записан празен фийд: {} поради грешка: {}".format(filepath, e))


if __name__ == "__main__":
    create_dnes_feed("dnes.xml", max_items=20)
