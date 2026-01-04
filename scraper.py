import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import os
from urllib.parse import urljoin, urlparse


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


def pick_links_generic(soup: BeautifulSoup, base_url: str):
    """Fallback: всички <a>, но с базова филтрация."""
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not is_good_href(base_url, href):
            continue
        title = normalize_title(a.get_text(" ", strip=True)) or normalize_title(a.get("title", ""))
        yield title, urljoin(base_url, href)


def pick_links_econ(soup: BeautifulSoup, base_url: str):
    """
    Econ.bg листингът (Новини) съдържа последователни блокове "Заглавие + дата + откъс".
    Тук първо се опитваме да вземем линковете от основната секция около заглавието "Новини".
    Ако структурата се промени, ще паднем на generic fallback.
    """
    # Намери "Новини" хедъра и вземи линковете след него (в близките елементи)
    header = soup.find(lambda t: t.name in ("h1", "h2", "div") and "Новини" in t.get_text(" ", strip=True))
    if not header:
        return []

    # Вземаме линковете в следващия голям контейнер (след хедъра)
    container = header.find_parent()
    if not container:
        return []

    links = []
    for a in container.find_all("a", href=True):
        href = a.get("href")
        if not is_good_href(base_url, href):
            continue
        title = normalize_title(a.get_text(" ", strip=True)) or normalize_title(a.get("title", ""))
        if title:
            links.append((title, urljoin(base_url, href)))

    return links


def create_feed(target_url, source_name, filename, max_items=20, min_title_len=8):
    os.makedirs("feeds", exist_ok=True)
    filepath = os.path.join("feeds", filename)

    fg = FeedGenerator()
    fg.id(target_url)
    fg.title(f"Новини от {source_name}")
    fg.link(href=target_url, rel="alternate")
    fg.description(f"Автоматичен фийд за {source_name}")
    fg.language("bg")

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(target_url, headers=headers, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # 1) Опит със специфичен парсер за Econ.bg
        candidates = []
        if "econ.bg" in target_url:
            candidates = pick_links_econ(soup, target_url)

        # 2) Fallback към generic
        if not candidates:
            candidates = list(pick_links_generic(soup, target_url))

        seen = set()
        items_found = 0

        for title, link in candidates:
            title = normalize_title(title)

            if len(title) < min_title_len:
                continue
            if link in seen:
                continue
            seen.add(link)

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
    create_feed("https://econ.bg/Новини_l.al_at.1.html", "Econ.bg", "econ.xml", max_items=20, min_title_len=8)
    create_feed("https://www.dnes.bg/", "Dnes.bg", "dnes.xml", max_items=20, min_title_len=8)
