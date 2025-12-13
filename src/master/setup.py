import redis
import logging
import json
import logging.config

# Functions
def setup_redis_connection():
    try:
        redis_connection = redis.Redis(host=QUEUE_CONFIG['host'], port=QUEUE_CONFIG['port'], decode_responses=True)
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
    logger = setup_logging("MASTER.setup")
    logger.info("Logger configuration loaded")

    QUEUE_CONFIG = json.load(open('src/cfg/queue.json'))
    logger.info("Queue configuration loaded")

    redis_connection = setup_redis_connection()
    groups = QUEUE_CONFIG.get("consumer_groups", [])
    logger.info(f"Queue configuration loaded")

    for group in groups:
        create_consumer_group(redis_connection, group, QUEUE_CONFIG.get("stream_name"))
        
    logger.info("Setup completed successfully")

except FileNotFoundError as e:
    print(f"Configuration file not found: {e}")
    raise e

except json.JSONDecodeError as e:
    print(f"Error decoding JSON configuration: {e}")
    raise e

except redis.exceptions.ConnectionError as e:
    print(f"Redis connection error: {e}")
    raise e

except redis.exceptions.ResponseError as e:
    print(f"Redis response error: {e}")
    raise e

except Exception as e:
    print(f"Setup failed: {e}")
    raise e
