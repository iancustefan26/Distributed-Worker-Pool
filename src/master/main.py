from master.setup import redis_connection, setup_logging
from master import helper
import logging

logger = setup_logging("MASTER.main")

def main():
    logger.info("Starting Master Node")
    if helper.try_ping_redis(redis_connection):
        logger.info("Redis is reachable")
    else:
        logger.error("Redis is not reachable")
    
if __name__ == "__main__":
    main()