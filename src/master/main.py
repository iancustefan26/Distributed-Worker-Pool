from master.setup import redis_connection, setup_logging, QUEUE_CONFIG
from master import helper
import logging
from master.helper import enqueue_random_jobs

logger = setup_logging("MASTER.main")

def main():
    logger.info("Starting Master Node")
    try:
        helper.try_ping_redis(redis_connection)
        logger.info("Redis is reachable")

        enqueue_random_jobs(redis_connection, QUEUE_CONFIG['stream_name'], logger)
        
    except Exception as e:
        logger.exception(f"Failed to reach Redis: {e}")
        return

    
if __name__ == "__main__":
    main()