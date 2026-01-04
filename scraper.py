import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime

def generate_rss():
    fg = FeedGenerator()
    fg.id('http://example.com')
    fg.title('Моят RSS Фийд')
    fg.link(href='http://example.com', rel='alternate')
    fg.description('Автоматизиран фийд')

    # Пример за скрапване (тук се сменя адреса)
    url = "https://econ.bg/Новини_l.al_at.1.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Тук скриптът търси линкове на страницата
        for a in soup.find_all('a', href=True)[:10]:
            if 'Новини' in a['href']:
                fe = fg.add_entry()
                fe.id(a['href'])
                fe.title(a.text.strip() if a.text else "Новина")
                fe.link(href=a['href'])
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
        
        fg.rss_file('feed.xml')
    except Exception as e:
        print(f"Грешка: {e}")

if __name__ == "__main__":
    generate_rss()