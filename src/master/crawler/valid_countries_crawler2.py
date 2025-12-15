import re
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


# ======================
# Load config
# ======================

CONFIG_PATH = "src/cfg/crawler.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

COUNTRY_API = CONFIG["country_api"]
SEMRUSH_CFG = CONFIG["semrush_valid_countries"]


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())

def build_country_index():
    resp = requests.get(
        COUNTRY_API["url"],
        params=COUNTRY_API.get("params", {}),
        timeout=30
    )
    resp.raise_for_status()

    alias_to_country = {}
    canonical = {}

    for c in resp.json():
        common = c["name"]["common"]
        canonical[common] = common

        aliases = set()
        aliases.add(common)
        aliases.add(slugify(common))
        aliases.add(normalize(common))

        for alt in c.get("altSpellings", []):
            aliases.add(alt)
            aliases.add(slugify(alt))
            aliases.add(normalize(alt))

        aliases.add(c.get("cca2"))
        aliases.add(c.get("cca3"))

        for a in aliases:
            if a:
                alias_to_country[a.lower()] = common

    return alias_to_country, canonical


# ======================
# SEMrush probing logic
# ======================

BASE_URL = SEMRUSH_CFG["base_url"]
HEADERS = SEMRUSH_CFG.get("headers", {})
OUTPUT_DIR = Path(SEMRUSH_CFG.get("output_dir", "."))
OUTPUT_FILE = OUTPUT_DIR / SEMRUSH_CFG["output_file"]
MAX_WORKERS = 30  # ✅ as requested

alias_to_country, _ = build_country_index()

def semrush_url_exists(country_slug: str):
    url = BASE_URL.format(country=country_slug)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code == 200:
            return url
    except requests.RequestException:
        pass
    return None

def scan_countries():
    tested = set()
    slugs = []

    for alias in alias_to_country.keys():
        slug = slugify(alias)
        if slug and slug not in tested:
            tested.add(slug)
            slugs.append(slug)

    valid_links = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(semrush_url_exists, slug)
            for slug in slugs
        ]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Checking SEMrush countries",
            unit="country"
        ):
            result = future.result()
            if result:
                valid_links.append(result)

    return valid_links


# ======================
# Main
# ======================

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = scan_countries()

    OUTPUT_FILE.write_text("\n".join(sorted(results)), encoding="utf-8")

    print("\nRESULT:")
    print(f"Saved {len(results)} valid links to {OUTPUT_FILE}")
