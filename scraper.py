import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import os
import re
from urllib.parse import urljoin, urlparse


HEADERS = {"User-Agent": "Mozilla/5.0"}


def normalize_title(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split()).strip()


def is_good_href(base_url: str, href: str) -> bool:
    if not href:
        return False
    if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
        return False
    absolute = urljoin(base_url, href)
    p = urlparse(absolute)
    return p.scheme in ("http", "https")


def pick_generic_links(soup: BeautifulSoup, base_url: str):
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not is_good_href(base_url, href):
            continue
        title = normalize_title(a.get_text(" ", strip=True)) or normalize_title(a.get("title", ""))
        yield title, urljoin(base_url, href)


def pick_dnes(soup: BeautifulSoup, base_url: str):
    # На dnes.bg заглавията на началната често излизат като H3/### блокове в текста [page:1]
    out = []
    for h in soup.find_all(["h3", "h2", "a"]):
        # търсим “новинарски” заглавия с достатъчно дължина
        a = h if h.name == "a" else h.find("a")
        if not a or not a.get("href"):
            continue
        title = normalize_title(a.get_text(" ", strip=True))
        if len(title) < 8:
            continue
        link = urljoin(base_url, a["href"])
        out.append((title, link))
    return out


def pick_econ_from_listing_text(soup: BeautifulSoup, base_url: str):
    """
    Econ.bg листингът съдържа ясно видими заглавия и дати във формат:
    '06.03.2025 | 15:30' след заглавие. [page:1]
    Идея: намираме всички <a> с текст и после ги филтрираме като “заглавия”,
    но използваме и регекса за дата, за да предпочетем линкове около такива блокове.
    """
    date_re = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\s*\|\s*\d{2}:\d{2}\b")
    text = soup.get_text("\n", strip=True)

    # Ако страницата очевидно съдържа много блокове с дата, приемаме че сме на листинг [page:1]
    has_listing_dates = len(date_re.findall(text)) >= 5

    out = []
    for a in soup.find_all("a", href=True):
        title = normalize_title(a.get_text(" ", strip=True))
        if len(title) < 8:
            continue

        href = a.get("href")
        if not is_good_href(base_url, href):
            continue

        link = urljoin(base_url, href)

        # Ако сме в листинг, допускаме повече заглавия; иначе ще е по-шумно
        if has_listing_dates:
            out.append((title, link))
        else:
            # по-строго ако не изглежда като листинг
            if len(title) >= 15:
                out.append((title, link))

    return out


def create_feed(target_url, source_name, filename, max_items=20, min_title_len=8):
    os.makedirs("feeds", exist_ok=True)
    filepath = os.path.join("feeds", filename)

    fg = FeedGenerator()
    fg.id(target_url)
    fg.title(f"Новини от {source_name}")
    fg.link(href=target_url, rel="alternate")
    fg.description(f"Автоматичен фийд за {source_name}")
    fg.language("bg")

    try:
        r = requests.get(target_url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # 1) Специфичен парсер по сайт
        candidates = []
        if "econ.bg" in target_url:
            candidates = pick_econ_from_listing_text(soup, target_url)
        elif "dnes.bg" in target_url:
            candidates = pick_dnes(soup, target_url)

        # 2) Fallback (generic)
        if not candidates:
            candidates = list(pick_generic_links(soup, target_url))

        seen_links = set()
        seen_titles = set()
        items_found = 0

        for title, link in candidates:
            title = normalize_title(title)
            if len(title) < min_title_len:
                continue
            if link in seen_links:
                continue

            # намаляваме дубликати по заглавие (Dnes понякога повтаря)
            tkey = title.lower()
            if tkey in seen_titles:
                continue

            seen_links.add(link)
            seen_titles.add(tkey)

            fe = fg.add_entry()
            fe.id(link)
            fe.title(title)
            fe.link(href=link)
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

            items_found += 1
            if items_found >= max_items:
                break

        fg.rss_file(filepath)
        print(f"✅ Успех: {filepath} (items: {items_found})")

    except Exception as e:
        print(f"❌ Грешка за {source_name}: {e}")


if __name__ == "__main__":
    # 20 на сайт
    create_feed("https://econ.bg/Новини_l.al_at.1.html", "Econ.bg", "econ.xml", max_items=20, min_title_len=8)
    create_feed("https://www.dnes.bg/", "Dnes.bg", "dnes.xml", max_items=20, min_title_len=8)
