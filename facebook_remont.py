import os
import requests

RUN_ID = "be034YkD3QrVX2d5W"
OUT_FILE = "feeds/facebook-remont.xml"

def main():
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing APIFY_TOKEN")

    os.makedirs("feeds", exist_ok=True)

    # Взима items от dataset-а на конкретния run (JSON).
    # Ако искаш директно RSS от Apify, можем да сменим format=rss.
    url = f"https://api.apify.com/v2/actor-runs/{RUN_ID}/dataset/items"
    params = {
        "token": token,
        "format": "json",
        "clean": "true",
        "limit": "30",
    }

    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    items = r.json()

    # Генерираме прост RSS файл (минимален RSS 2.0)
    # (Без feedgen, за да няма зависимости.)
    def esc(s):
        return (
            (s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    rss_items = []
    for it in items[:30]:
        title = esc(str(it.get("text") or it.get("title") or "Facebook post")[:150])
        link = esc(it.get("url") or it.get("postUrl") or "")
        if not link:
            continue
        rss_items.append(
            f"<item><title>{title}</title><link>{link}</link><guid>{link}</guid></item>"
        )

    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<rss version=\"2.0\"><channel>"
        "<title>Как да направя ремонт у дома?</title>"
        "<link>https://www.facebook.com/groups/299913907483894/</link>"
        "<description>Емисия от Facebook група (Apify)</description>"
        f"{''.join(rss_items)}"
        "</channel></rss>"
    )

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(rss)

    print(f"✅ Wrote {OUT_FILE} (items: {len(rss_items)})")

if __name__ == "__main__":
    main()
