from helpers.setup import redis_connection, setup_logging, QUEUE_CONFIG
from helpers import helper
import logging
from helpers.helper import dequeue_job_group, ack_job
import time

logger = setup_logging("Worker.main")

def main():
    logger.info("Starting Worker Node")
    try:
        helper.try_ping_redis(redis_connection)
        logger.info("Redis is reachable")

        while True:
            result = dequeue_job_group(
                redis_connection,
                stream_name=QUEUE_CONFIG['stream_name'],
                group_name=QUEUE_CONFIG['consumer_groups'][0],

                # get the docker hostname as consumer name
                consumer_name= helper.get_hostname()
            )

            if not result:
                continue

            job, message_id = result

            logger.info(f"Processing {message_id} : {job['payload']['link']}")

            time.sleep(6)
            # do work here ...

            ack_job(redis_connection, "job_stream", "workers", message_id)

        
    except Exception as e:
        logger.exception(f"Failed to reach Redis: {e}")
        return

    
if __name__ == "__main__":
    main()