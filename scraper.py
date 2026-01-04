import datetime
import os

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator


DNES_LAST_ARTICLES_URL = "https://www.dnes.bg/last-articles"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def normalize_title(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split()).strip()


def create_dnes_feed(filename: str = "dnes.xml", max_items: int = 20):
    os.makedirs("feeds", exist_ok=True)
    filepath = os.path.join("feeds", filename)

    fg = FeedGenerator()
    fg.id(DNES_LAST_ARTICLES_URL)
    fg.title("Новини от Dnes.bg")
    fg.link(href=DNES_LAST_ARTICLES_URL, rel="alternate")
    fg.description("Автоматичен фийд (последни статии) от Dnes.bg")
    fg.language("bg")

    try:
        r = requests.get(DNES_LAST_ARTICLES_URL, headers=HEADERS, timeout=25)
        r.raise_for_status()

        soup = BeautifulSoup(r.content, "html.parser")

        # В /last-articles заглавията са като markdown-ish "### ..." в текста. [page:0]
        titles = []
        for line in soup.get_text("\n", strip=True).splitlines():
            line = line.strip()
            if line.startswith("###"):
                t = normalize_title(line.lstrip("#"))
                if t:
                    titles.append(t)

        # Дедупликация, запазвайки реда
        seen = set()
        unique_titles = []
        for t in titles:
            key = t.lower()
            if key in seen:
                continue
            seen.add(key)
            unique_titles.append(t)

        # Добавяме до max_items. (Без линкове, за да няма грешни препратки.) [page:0]
        for t in unique_titles[:max_items]:
            fe = fg.add_entry()
            fe.id(f"{DNES_LAST_ARTICLES_URL}#{t}")
            fe.title(t)
            fe.link(href=DNES_LAST_ARTICLES_URL)
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        fg.rss_file(filepath)
        print(f"✅ Успех: {filepath} (items: {min(len(unique_titles), max_items)})")

    except Exception as e:
        # Винаги създаваме файла, дори при временен проблем
        fg.description(f"Грешка при извличане: {e}")
        fg.rss_file(filepath)
        print(f"⚠️ Записан празен фийд: {filepath} поради грешка: {e}")


if __name__ == "__main__":
    create_dnes_feed("dnes.xml", max_items=20)
