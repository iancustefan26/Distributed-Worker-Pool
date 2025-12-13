import redis
import logging
import json
import logging.config

# Functions
def setup_redis_connection():
    try:
        redis_connection = redis.Redis(host='redis', port=6379, decode_responses=True)
        logger.info("Connected to Redis")
    except redis.exceptions.ConnectionError as e:
        logger.exception(f"Redis connection failed: {e}")
        raise e
    
    return redis_connection

def create_consumer_group(redis_connection, group_name, stream_name):
    try:
        # Create a consumer group, also creates the stream if it doenst exist
        redis_connection.xgroup_create('job_queue', 'worker_group', id='0-0', mkstream=True)
        logger.info("Consumer group 'worker_group' created on stream 'job_queue'")
    except redis.exceptions.ResponseError as e:
        logger.warning(f"Creating consumer group 'worker_group' failed : {e}")

def setup_logging(name):
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger(name)


# Setup phase
try:
    LOGGING_CONFIG = json.load(open('src/cfg/logging.json'))
    QUEUE_CONFIG = json.load(open('src/cfg/queue.json'))
    logger = setup_logging("MASTER.setup")


    redis_connection = setup_redis_connection()
    groups = QUEUE_CONFIG.get("consumer_groups", [])
    for group in groups:
        create_consumer_group(redis_connection, group, QUEUE_CONFIG.get("stream_name"))
except Exception as e:
    print(f"Setup failed: {e}")
    raise e
