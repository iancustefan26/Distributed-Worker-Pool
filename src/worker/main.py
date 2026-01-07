from helpers.setup import redis_connection, setup_logging, QUEUE_CONFIG
from helpers import helper
from helpers.helper import try_ping_redis, get_hostname
from worker.crawler import download_and_save
from helpers.helper import dequeue_job_group, ack_job
import time
from requests.exceptions import HTTPError

logger = setup_logging("Worker.main")

def main():
    """
    Main worker loop that continuously processes jobs from a Redis stream.

    The worker initializes logging, verifies Redis connectivity, and then enters
    an infinite loop where it dequeues job groups from a configured Redis stream
    consumer group. For each received job, it logs metadata, executes the
    download-and-save operation, and acknowledges successful jobs back to Redis.

    Jobs that fail due to HTTP-related errors are logged and left unacknowledged
    to allow retries, while unexpected exceptions are treated as permanent
    failures and logged accordingly. If the worker encounters a fatal error
    outside the processing loop, it logs the crash details before exiting.
    """

    logger.info("Starting Worker Node")

    try:
        try_ping_redis(redis_connection)
        logger.info("Redis is reachable")

        while True:
            result = dequeue_job_group(
                redis_connection,
                stream_name=QUEUE_CONFIG["stream_name"],
                group_name=QUEUE_CONFIG["consumer_groups"][0],
                consumer_name=get_hostname()
            )

            if not result:
                time.sleep(0.5)
                continue

            job, message_id = result
            payload = job["payload"]
            print(payload)
            logger.info(
                f"Processing job {message_id} → {payload['domain']} "
                f"(country={payload['statistics']['country']}, position={payload['statistics']['position']})"
            )

            try:
                download_and_save(job, logger)

                ack_job(
                    redis_connection,
                    QUEUE_CONFIG["stream_name"],
                    QUEUE_CONFIG["consumer_groups"][0],
                    message_id
                )

                logger.info(f"ACKED job {message_id}")
            
            except HTTPError as e:
                logger.warning(f"Job {message_id} failed with HTTPError: {e}. Will retry later.")

            except Exception as e:
                logger.exception(f"Job {message_id} failed permanently: {e}")

    except Exception as e:
        logger.exception(f"Worker crashed: {e}")

    
if __name__ == "__main__":
    main()