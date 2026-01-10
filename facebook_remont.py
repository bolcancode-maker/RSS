import os
import datetime
import requests

DATASET_ID = "rnVwfZ0MpXmbzBten"
OUT_FILE = "feeds/facebook-remont.xml"
GROUP_LINK = "https://www.facebook.com/groups/299913907483894/"

def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def write_error_rss(msg: str):
    os.makedirs("feeds", exist_ok=True)
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Как да направя ремонт у дома?</title>
  <link>{GROUP_LINK}</link>
  <description>{esc(msg)}</description>
</channel></rss>'''
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(rss)

def main():
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        write_error_rss("Missing APIFY_TOKEN")
        return

    os.makedirs("feeds", exist_ok=True)

    url = f"https://api.apify.com/v2/datasets/{DATASET_ID}/items"
    params = {
        "token": token,
        "format": "json",
        "clean": "true",
        "limit": "30",
        "desc": "1",   # най-новите първо
    }

    try:
        r = requests.get(url, params=params, timeout=120)
        r.raise_for_status()
        items = r.json()

        now = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
        rss_items = []

        for it in items:
            link = it.get("url") or ""
            title = (it.get("text") or "Facebook пост").strip().splitlines()[0][:120]
            if not link:
                continue
            rss_items.append(
                f"<item>"
                f"<title>{esc(title)}</title>"
                f"<link>{esc(link)}</link>"
                f"<guid>{esc(link)}</guid>"
                f"<pubDate>{now}</pubDate>"
                f"</item>"
            )

        rss = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<rss version="2.0"><channel>'
            '<title>Как да направя ремонт у дома?</title>'
            f'<link>{esc(GROUP_LINK)}</link>'
            '<description>Емисия от Facebook група (Apify dataset)</description>'
            + "".join(rss_items) +
            '</channel></rss>'
        )

        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss)

    except Exception as e:
        write_error_rss(f"Dataset fetch error: {e}")

if __name__ == "__main__":
    main()
