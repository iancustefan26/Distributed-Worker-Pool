import requests
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
import socket
from master.helper import enqueue_job

INPUT_FILE = "semrush_valid_country_links.txt"
OUTPUT_FILE = "semrush_top20_results.json"
TOP_X = 20
CRAWL_CFG_PATH = "src/cfg/crawler.json"
QUEUE_CFG_PATH = "src/cfg/queue.json"

with open(CRAWL_CFG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

with open(QUEUE_CFG_PATH, "r", encoding="utf-8") as f:
    QUEUE_CONFIG = json.load(f)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SemrushCrawler/1.0)"
}

def parse_number(value):
    if not value:
        return None
    return int(value.replace(",", "").strip())

def parse_float(value):
    try:
        return float(value.strip())
    except:
        return None

def extract_table_data(html):
    soup = BeautifulSoup(html, "html.parser")
    tbody = soup.find("tbody", {"data-test": "Body"})

    if not tbody:
        return []

    rows = tbody.find_all("tr", limit=TOP_X)
    results = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue

        # Position
        pos_tag = row.find("span", itemprop="position")
        position = int(pos_tag["content"]) if pos_tag else None

        # Domain + URL
        link = row.find("a", itemprop="url")
        domain = link.find("span", itemprop="name").text.strip()
        semrush_url = link["href"]

        # Rank change (arrow up/down)
        change_cell = cells[2]
        arrow = change_cell.find("svg")
        change_value = change_cell.find("span", {"data-ui-name": "Text"})
        rank_change = None

        if arrow and change_value:
            direction = "up" if "ArrowUp" in arrow["data-ui-name"] else "down"
            rank_change = f"{direction} {change_value.text.strip()}"

        # Stats
        traffic = parse_number(cells[3].text)
        pages_per_visit = parse_float(cells[4].text)
        bounce_rate = cells[5].text.strip()

        results.append({
            "domain": domain,
            "position": position,
            "traffic": traffic,
            "pages_per_visit": pages_per_visit,
            "bounce_rate": bounce_rate,
            "rank_change": rank_change
        })

    return results


def crawl_and_enqueue_jobs(connection, stream_name, logger):
    all_jobs = []
    retry_jobs = []

    now = datetime.now()
    month = now.strftime("%Y-%m")
    machine = socket.gethostname()
    created_by = f"master_node_{machine}"

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    for idx, url in enumerate(urls, start=1):
        logger.info(f"[{idx}/{len(urls)}] Crawling: {url}")

        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()

            results = extract_table_data(r.text)

            # Create job
            country = urlparse(url).path.split("/")[4]
            created_at = now.isoformat()

            for row in results:
                domain = row["domain"]
                link = f"https://{domain}"

                job = {
                    "metadata": {
                        "created_at": created_at,
                        "created_by": created_by
                    },
                    "payload": {
                        "domain": domain,
                        "link": link,
                        "request_method": "GET",
                        "headers": HEADERS,
                        "body": None,
                        "download_paths": [
                            f"~/downloads/{month}/{country}/top_{row.get('position')}"
                        ],
                        "statistics": {
                            "country": country,
                            "month": month,
                            "position": row.get("position"),
                            "traffic": row.get("traffic"),
                            "pages_per_visit": row.get("pages_per_visit"),
                            "bounce_rate": row.get("bounce_rate"),
                            "rank_change": row.get("rank_change")
                        }
                    }
                }

                try:
                    enqueue_job(
                        connection=connection,
                        stream_name=stream_name,
                        job=job,
                        logger=logger
                    )
                except Exception as e:
                    logger.exception(f"Failed to enqueue job for {domain}: {e}")
                    retry_jobs.append(job)

                    continue

                all_jobs.append(job)

            logger.info(f"Extracted and enqueued {len(results)} jobs from {url}")
            logger.info("Waiting before next request... (to respect rate limits from robots.txt)")

            time.sleep(
                CONFIG["semrush_valid_countries"]["wait_between_requests"]
            )

        except Exception as e:
             logger.exception(f"Failed to crawl {url}: {e}")
             continue
        
    logger.info(f"\nCrawling completed. Total jobs created: {len(all_jobs)}")
    
    if retry_jobs:
        logger.warning(f"{len(retry_jobs)} jobs failed to enqueue. Retrying...")

    for _ in range(QUEUE_CONFIG.get("retries_limit", 3)):
        logger.info(f"Retry attempt {_ + 1}")
        failed = []
        for job in retry_jobs:
            logger.info(f"Retrying enqueue job for {job['payload']['link']}")
            try:
                enqueue_job(
                    connection=connection,
                    stream_name=stream_name,
                    job=job,
                    logger=logger
                )
                
            except Exception as e:
                logger.exception(f"Retry failed for job {job['payload']['link']}: {e}")
                failed.append(job)
                continue
        
        if not failed:
            logger.info("All retry jobs enqueued successfully.")
            break
        else:
            logger.warning(f"{len(failed)} jobs still failed to enqueue after retry.")
            retry_jobs = failed

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2)

    logger.info(f"\nDone. Created {len(all_jobs)} jobs → {OUTPUT_FILE}")

