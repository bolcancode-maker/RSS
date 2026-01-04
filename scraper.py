import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
from urllib.parse import urljoin

def create_feed(target_url, source_name, filename):
    fg = FeedGenerator()
    fg.id(target_url)
    fg.title(f'Новини от {source_name}')
    fg.link(href=target_url, rel='alternate')
    fg.description(f'Автоматичен фийд за {source_name}')
    fg.language('bg')

    headers = {'User-Agent': 'Mozilla/5.0'}
    
    seen_links = set()
    try:
        response = requests.get(target_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, 'html.parser')
        for tag in soup.find_all(['h2', 'h3', 'a']):
            a_tag = tag if tag.name == 'a' else tag.find('a')
            if a_tag and a_tag.get('href'):
                link = urljoin(target_url, a_tag['href'])
                title = a_tag.text.strip()
                if len(title) > 25 and link not in seen_links:
                    seen_links.add(link)
                    fe = fg.add_entry()
                    fe.id(link)
                    fe.title(title)
                    fe.link(href=link)
                    fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                    if len(seen_links) >= 20: break
        fg.rss_file(filename)
        print(f"Успех за {filename}")
    except Exception as e:
        print(f"Грешка: {e}")

if __name__ == "__main__":
    create_feed("https://econ.bg/Новини_l.al_at.1.html", "Econ.bg", "econ.xml")
    create_feed("https://www.dnes.bg/", "Dnes.bg", "dnes.xml")
