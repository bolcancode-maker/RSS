import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import os
from urllib.parse import urljoin


def create_feed(target_url, source_name, filename):
    os.makedirs("feeds", exist_ok=True)
    filepath = os.path.join("feeds", filename)

    fg = FeedGenerator()
    fg.id(target_url)
    fg.title(f"Новини от {source_name}")
    fg.link(href=target_url, rel="alternate")
    fg.description(f"Автоматичен фийд за {source_name}")
    fg.language("bg")

    headers = {"User-Agent": "Mozilla/5.0"}
    seen_links = set()

    try:
        response = requests.get(target_url, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        items_found = 0
        for tag in soup.find_all(["h2", "h3", "a"]):
            a_tag = tag if tag.name == "a" else tag.find("a")
            if not a_tag or not a_tag.get("href"):
                continue

            link = urljoin(target_url, a_tag["href"])
            title = a_tag.get_text(" ", strip=True)

            if len(title) > 25 and link not in seen_links:
                seen_links.add(link)
                fe = fg.add_entry()
                fe.id(link)
                fe.title(title)
                fe.link(href=link)
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                items_found += 1
                if items_found >= 20:
                    break

        fg.rss_file(filepath)
        print(f"✅ Успех: {filepath}")
    except Exception as e:
        print(f"❌ Грешка: {e}")


if __name__ == "__main__":
    create_feed("https://econ.bg/Новини_l.al_at.1.html", "Econ.bg", "econ.xml")
    create_feed("https://www.dnes.bg/", "Dnes.bg", "dnes.xml")
