import os
import requests

ACTOR_ID = "2chN8UQcH1CfxLRNE"
GROUP_URL = "https://www.facebook.com/groups/299913907483894/"
OUT_FILE = "feeds/facebook-remont.xml"

def main():
    token = os.environ.get("APIFY_TOKEN", "").strip()
    os.makedirs("feeds", exist_ok=True)

    if not token:
        # Записваме празен файл, за да има какво да commit-не
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
                    '<title>Как да направя ремонт у дома?</title>'
                    '<description>Missing APIFY_TOKEN</description>'
                    '</channel></rss>')
        return

    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = {"token": token, "format": "rss", "clean": "true", "limit": "30"}
    payload = {"facebookUrl": GROUP_URL}

    r = requests.post(url, params=params, json=payload, timeout=300)

    if r.status_code >= 400:
        # Пак записваме файл, но с грешката
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
                    '<title>Как да направя ремонт у дома?</title>'
                    f'<description>Apify error {r.status_code}: {r.text[:200]}</description>'
                    '</channel></rss>')
        return

    # Това е ключовото: запис на върнатия RSS
    with open(OUT_FILE, "wb") as f:
        f.write(r.content)

    print(f"✅ Saved {OUT_FILE}")

if __name__ == "__main__":
    main()
