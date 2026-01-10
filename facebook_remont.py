import datetime
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

FACEBOOK_GROUP_URL = "https://www.facebook.com/groups/299913907483894/"
OUT_FILE = "facebook-remont.xml"

def norm(text: str) -> str:
    return " ".join((text or "").split()).strip()

def create_facebook_feed(max_items: int = 15):
    token = os.environ.get("SCRAPEDO_TOKEN", "").strip()

    os.makedirs("feeds", exist_ok=True)
    filepath = os.path.join("feeds", OUT_FILE)

    fg = FeedGenerator()
    fg.id(FACEBOOK_GROUP_URL)
    fg.title("Как да направя ремонт у дома?")
    fg.link(href=FACEBOOK_GROUP_URL, rel="alternate")
    fg.description("Емисия от Facebook група (през scrape.do).")
    fg.language("bg")

    if not token:
        fg.description("Липсва SCRAPEDO_TOKEN (GitHub Secret).")
        fg.rss_file(filepath)
        print(f"⚠️ {filepath} (missing token)")
        return

    r = requests.get(
        "http://api.scrape.do/",
        params={"url": FACEBOOK_GROUP_URL, "token": token},
        timeout=60,
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    items = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/groups/" not in href or "/posts/" not in href:
            continue

        link = urljoin("https://www.facebook.com", href)
        if link in seen:
            continue

        title = norm(a.get_text(" ", strip=True)) or "Facebook пост"
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

if __name__ == "__main__":
    create_facebook_feed(max_items=15)
