import os
import requests

ACTOR_ID = "2chN8UQcH1CfxLRNE"
GROUP_URL = "https://www.facebook.com/groups/299913907483894/"
OUT_FILE = "feeds/facebook-remont.xml"

def main():
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing APIFY_TOKEN")

    os.makedirs("feeds", exist_ok=True)

    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = {
        "token": token,
        "format": "rss",
        "clean": "true",
        "limit": "30",
    }

    # Input към actor-а: Group url = facebookUrl
    payload = {
        "facebookUrl": GROUP_URL
    }

    r = requests.post(url, params=params, json=payload, timeout=300)
    r.raise_for_status()

    with open(OUT_FILE, "wb") as f:
        f.write(r.content)

    print(f"✅ Wrote {OUT_FILE}")

if __name__ == "__main__":
    main()
