import redis
import json
import random
import time
from datetime import datetime

def try_ping_redis(connection):
    try:
        connection.ping()
    except redis.exceptions.ConnectionError as e:
        raise e

# -----------------------------
# Random data pools
# -----------------------------
USERS = ["system", "crawler", "scheduler", "worker-1"]
COUNTRIES = ["US", "DE", "FR", "IN", "BR"]
CATEGORIES = ["news", "sports", "tech", "finance"]
TOPICS = ["google", "amazon", "openai", "netflix"]
DOMAINS = ["example.com", "news.com", "api.service.io"]
METHODS = ["GET", "POST"]
USER_AGENTS = [
    "Mozilla/5.0",
    "curl/8.0",
    "python-requests/2.31"
]

# -----------------------------
# Helper functions
# -----------------------------
def random_job():
    now = datetime.now()
    month = now.strftime("%Y-%m")

    country = random.choice(COUNTRIES)
    category = random.choice(CATEGORIES)
    top = random.choice(TOPICS)
    domain = random.choice(DOMAINS)
    method = random.choices(METHODS, weights=[0.8, 0.2])[0]

    payload = {
        "domain": domain,
        "link": f"https://{domain}/{category}/{top}",
        "request_method": method,
        "download_paths": [
            f"downloads/{month}/{country}/{category}/{top}",
            f"downloads/{month}/{country}/{top}"
        ]
    }

    # Only add headers/body for non-GET requests
    if method != "GET":
        payload["headers"] = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip",
            "Connection": "keep-alive"
        }
        payload["body"] = json.dumps({"query": top})

    return {
        "metadata": {
            "created_at": now.isoformat(),
            "created_by": random.choice(USERS),
            "country": country,
            "category": category,
            "top": top,
            "month": month
        },
        "payload": payload
    }


# -----------------------------
# Main enqueue function
# -----------------------------
def enqueue_random_jobs(connection: redis.Redis, stream_name, logger):
    """
    Continuously enqueue random jobs into a Redis Stream every 5 seconds.
    """
    while True:
        job = random_job()

        # Redis Streams expect flat key-value pairs
        logger.info(f"Generated job: {job}")
        id = connection.xadd(
            name = stream_name,
            id = '*',
            fields = {"download_job" : json.dumps(job)}
        )

        logger.info(f"Enqueued random job:{id} → : { job['metadata']['category']} / {job['payload']['request_method']}")
        time.sleep(0.05)


def enqueue_job(connection: redis.Redis, stream_name, job, logger):
    """
    Enqueue a specific job into a Redis Stream.
    """
    # Redis Streams expect flat key-value pairs
    logger.info(f"Enqueuing job: {job}")
    id = connection.xadd(
        name = stream_name,
        id = '*',
        fields = {"download_job" : json.dumps(job)}
    )

    logger.info(f"Enqueued job:{id} → : { job['metadata']} / {job['payload']['domain']}")
    return id

