import json
import os
import time
import logging
import requests

CFG_PATH = "src/cfg/crawler.json"
with open(CFG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

MAX_RETRIES = CONFIG.get("download_retries", 3)
RETRY_BACKOFF = CONFIG.get("retry_backoff", 5)  
REQUEST_TIMEOUT = CONFIG.get("request_timeout", 30)  

def download_and_save(job: dict, logger: logging.Logger):
    payload = job["payload"]

    url = payload["link"]
    headers = payload.get("headers", {})
    method = payload.get("request_method", "GET").upper()
    download_paths = payload["download_paths"]

    if method != "GET":
        raise ValueError(f"Unsupported request method: {method}")

    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Fetching [{attempt}/{MAX_RETRIES}]: {url}")

            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            html = response.text

            for path in download_paths:
                os.makedirs(path, exist_ok=True)
                file_path = os.path.join(path, "index.html")

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html)

                logger.info(f"Saved page → {file_path}")

            return

        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} failed for {url}: {e}")
            time.sleep(RETRY_BACKOFF * attempt)

    raise last_exception
