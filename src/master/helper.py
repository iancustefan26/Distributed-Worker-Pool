import redis
import json
import random
import time
from datetime import datetime

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


def try_ping_redis(connection):
    """
    Check connectivity to a Redis server.

    This function sends a ping command to the provided Redis connection to verify
    that the server is reachable. If the connection fails, the underlying Redis
    connection error is raised.

    :param connection: Active Redis connection instance.
    :raises redis.exceptions.ConnectionError: If the Redis server is unreachable.
    """
    try:
        connection.ping()
    except redis.exceptions.ConnectionError as e:
        raise e
    
def random_job():
    """
    Generate a randomized job payload for testing or simulation purposes.

    This function constructs a job containing randomized metadata and payload
    information such as country, category, topic, domain, and HTTP method. The
    resulting job structure is suitable for enqueuing into a Redis stream and
    optionally includes request headers and body data for non-GET requests.

    :return: A dictionary representing a randomized job with metadata and payload.
    """

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


def enqueue_random_jobs(connection: redis.Redis, stream_name, logger):
    """
    Continuously enqueue randomly generated jobs into a Redis stream.

    This function runs in an infinite loop, generating random jobs and adding them
    to the specified Redis stream at a fixed interval. Each enqueued job is logged
    for traceability and debugging purposes.

    :param connection: Active Redis connection instance.
    :param stream_name: Name of the Redis stream to enqueue jobs into.
    :param logger: Logger instance used for logging job generation and enqueueing.
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
    Enqueue a single job into a Redis stream.

    This function serializes the provided job and adds it to the specified Redis
    stream. Upon successful enqueueing, the Redis message ID is logged and
    returned.

    :param connection: Active Redis connection instance.
    :param stream_name: Name of the Redis stream to enqueue the job into.
    :param job: Job dictionary containing metadata and payload information.
    :param logger: Logger instance used for logging enqueue operations.
    :return: Redis stream message ID of the enqueued job.
    """

    id = connection.xadd(
        name = stream_name,
        id = '*',
        fields = {"download_job" : json.dumps(job)}
    )

    logger.info(f"Enqueued job:{id} → : { job['metadata']} / {job['payload']['domain']}")
    return id

