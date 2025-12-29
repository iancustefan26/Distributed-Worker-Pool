from helpers.setup import redis_connection, setup_logging, QUEUE_CONFIG
from helpers import helper
from helpers.helper import try_ping_redis, get_hostname
from worker.crawler import download_and_save
from helpers.helper import dequeue_job_group, ack_job
import time
import requests
from requests.exceptions import HTTPError

logger = setup_logging("Worker.main")

def main():
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