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
        time.sleep(5)


def dequeue_job_group(
    connection,
    stream_name,
    group_name,
    consumer_name,
    block_ms=5000
):
    """
    Reads one job from a Redis Stream consumer group.
    Acknowledges after successful read.
    """
    response = connection.xreadgroup(
        group_name,
        consumer_name,
        {stream_name: ">"},
        count=1,
        block=block_ms
    )

    if not response:
        return None

    stream, messages = response[0]
    message_id, fields = messages[0]

    job = json.loads(fields['download_job'])

    return job, message_id

def ack_job(connection, stream_name, group_name, message_id):
    connection.xack(stream_name, group_name, message_id)


def get_hostname():
    import socket
    return socket.gethostname()