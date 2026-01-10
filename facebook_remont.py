import os
import requests

ACTOR_ID = "2chN8UQcH1CfxLRNE"
GROUP_URL = "https://www.facebook.com/groups/299913907483894/"
OUT_FILE = "feeds/facebook-remont.xml"

def write_error_rss(msg: str):
    os.makedirs("feeds", exist_ok=True)
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Как да направя ремонт у дома?</title>
  <link>{GROUP_URL}</link>
  <description>{msg}</description>
</channel></rss>'''
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(rss)

def main():
    token = os.environ.get("APIFY_TOKEN", "").strip()
    os.makedirs("feeds", exist_ok=True)

    if not token:
        write_error_rss("Missing APIFY_TOKEN")
        return

    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = {"token": token, "format": "rss", "clean": "true", "limit": "30"}

    payload = {
        "startUrls": [
            {"url": GROUP_URL}
        ]
    }

    try:
        r = requests.post(url, params=params, json=payload, timeout=300)
        if r.status_code >= 400:
            write_error_rss(f"Apify error {r.status_code}: {r.text[:300]}")
            return

        with open(OUT_FILE, "wb") as f:
            f.write(r.content)

        print(f"✅ Saved {OUT_FILE}")

    except Exception as e:
        write_error_rss(f"Exception: {e}")

if __name__ == "__main__":
    main()
