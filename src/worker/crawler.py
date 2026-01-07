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
    """
    Download a web page and save its contents and related statistics to disk.

    This function retrieves a URL specified in the job payload using an HTTP GET
    request, with configurable headers, timeout, and retry logic. On a successful
    response, the downloaded HTML content is saved as an index.html file in each
    configured download path, along with a statistics.json file containing
    associated metadata.

    The download operation is retried up to a maximum number of attempts using
    an exponential backoff strategy. If all attempts fail, the last encountered
    exception is raised.

    :param job: Dictionary containing the job payload with request details,
                download paths, and statistics.
    :param logger: Logger instance used for logging progress, warnings, and errors.
    :raises ValueError: If an unsupported HTTP request method is provided.
    :raises Exception: Re-raises the last exception if all retries fail.
    """

    payload = job["payload"]

    url = payload["link"]
    headers = payload.get("headers", {})
    method = payload.get("request_method", "GET").upper()
    download_paths = payload["download_paths"]

    statistics = payload.get("statistics", {})

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
                
                statistics_file = os.path.join(path, "statistics.json")
                with open(statistics_file, "w", encoding="utf-8") as f:
                    json.dump(statistics, f, indent=4)
                

                logger.info(f"Saved page → {file_path}")

            return

        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} failed for {url}: {e}")
            time.sleep(RETRY_BACKOFF * attempt)

    raise last_exception
