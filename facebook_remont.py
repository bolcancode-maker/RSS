import os
import requests

ACTOR_ID = "2chN8UQcH1CfxLRNE"  # твоят actor
OUT_FILE = "feeds/facebook-remont.xml"

def main():
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing APIFY_TOKEN")

    os.makedirs("feeds", exist_ok=True)

    # Run actor + return dataset items as RSS (sync; timeout ако надвиши ~300 сек)
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = {
        "token": token,
        "format": "rss",
        "clean": "true",
        "limit": "30",
    }

    # IMPORTANT: input-ът на actor-а е различен според кой actor точно ползваш.
    # Ако твоят actor вече има default settings за тази група, може да оставим празен input: {}
    # Ако иска URL, трябва да го сложим тук (примерно {"startUrls":[{"url":"..."}]}), но това зависи от actor input schema.
    r = requests.post(url, params=params, json={}, timeout=300)
    r.raise_for_status()

    with open(OUT_FILE, "wb") as f:
        f.write(r.content)

    print(f"✅ Wrote {OUT_FILE}")

if __name__ == "__main__":
    main()
