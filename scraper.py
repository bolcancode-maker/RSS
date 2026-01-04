import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
from urllib.parse import urljoin

def generate_rss():
    fg = FeedGenerator()
    fg.id('https://github.com/bolcancode-maker/RSS')
    fg.title('Новини: Econ.bg и Dnes.bg')
    fg.link(href='https://econ.bg', rel='alternate')
    fg.description('Комбиниран автоматизиран фийд')
    fg.language('bg')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    targets = [
        {"url": "https://econ.bg/Новини_l.al_at.1.html", "source": "Econ.bg"},
        {"url": "https://www.dnes.bg/", "source": "Dnes.bg"}
    ]

    for target in targets:
        try:
            response = requests.get(target["url"], headers=headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items_found = 0
            # Търсим всички връзки, които приличат на статии
            for tag in soup.find_all(['h2', 'h3', 'a']):
                link = tag.get('href') if tag.name == 'a' else (tag.find('a').get('href') if tag.find('a') else None)
                title = tag.text.strip()

                if link and len(title) > 25:
                    full_link = urljoin(target["url"], link)
                    
                    if any(x in full_link for x in ["facebook", "twitter", "linkedin", "google"]):
                        continue

                    fe = fg.add_entry()
                    fe.id(full_link)
                    fe.title(f"[{target['source']}] {title}")
                    fe.link(href=full_link)
                    # Използваме фиксирана дата, за да избегнем проблеми с часовите зони
                    fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                    
                    items_found += 1
                    if items_found >= 10:
                        break
            print(f"Успех за {target['source']}")
        except Exception as e:
            print(f"Грешка при {target['source']}: {e}")

    try:
        fg.rss_file('feed.xml')
        print("Файлът feed.xml е генериран успешно.")
    except Exception as e:
        print(f"Грешка при запис на файла: {e}")

if __name__ == "__main__":
    generate_rss()
