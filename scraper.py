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

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    seen_links = set()
    try:
        response = requests.get(target_url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        items_found = 0
        # Търсим заглавия в h1, h2, h3 и линкове
        for tag in soup.find_all(['h1', 'h2', 'h3', 'a']):
            a_tag = tag if tag.name == 'a' else tag.find('a')
            if not a_tag or not a_tag.get('href'):
                continue
            
            link = urljoin(target_url, a_tag['href'])
            title = a_tag.text.strip()

            # Филтри за качество и уникалност
            if len(title) > 25 and link not in seen_links:
                # Проверка за нежелани линкове
                if any(x in link for x in ["facebook.com", "twitter.com", "viber.com", "google.com"]):
                    continue
                
                seen_links.add(link)
                fe = fg.add_entry()
                fe.id(link)
                fe.title(title)
                fe.link(href=link)
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                
                items_found += 1
                if items_found >= 20: # Лимит от 20 новини на файл
                    break
        
        fg.rss_file(filename)
        print(f"✅ Успешно генериран: {filename} ({items_found} новини)")
    except Exception as e:
        print(f"❌ Грешка при {source_name}: {e}")

if __name__ == "__main__":
    # Дефинираме кои сайтове да се обработят
    create_feed("https://econ.bg/Новини_l.al_at.1.html", "Econ.bg", "econ.xml")
    create_feed("https://www.dnes.bg/", "Dnes.bg", "dnes.xml")
