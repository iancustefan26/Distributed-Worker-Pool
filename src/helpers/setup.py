import redis
import logging
import json
import logging.config

# Functions
def setup_redis_connection():
    """
    Establish and return a connection to the Redis server.

    This function initializes a Redis client using host and port information
    from the queue configuration. It logs a success message upon a successful
    connection and raises an exception if the connection attempt fails.

    :return: An active Redis connection instance.
    :raises redis.exceptions.ConnectionError: If the Redis server is unreachable.
    """
    try:
        redis_connection = redis.Redis(host=QUEUE_CONFIG['host'], port=QUEUE_CONFIG['port'], decode_responses=True)
        logger.info("Connected to Redis")
    except redis.exceptions.ConnectionError as e:
        logger.exception(f"Redis connection failed: {e}")
        raise e
    
    return redis_connection

def create_consumer_group(redis_connection, group_name, stream_name):
    """
    Create a Redis consumer group for a given stream.

    This function attempts to create a consumer group on the specified Redis
    stream. If the stream does not already exist, it is created automatically.
    If the consumer group already exists, a warning is logged instead of failing.

    :param redis_connection: Active Redis connection instance.
    :param group_name: Name of the consumer group to create.
    :param stream_name: Name of the Redis stream associated with the group.
    """
    try:
        # Create a consumer group, also creates the stream if it doenst exist
        redis_connection.xgroup_create(stream_name, group_name, id='0-0', mkstream=True)
        logger.info("Consumer group 'worker_group' created on stream 'job_queue'")
    except redis.exceptions.ResponseError as e:
        logger.warning(f"Creating consumer group 'worker_group' failed : {e}")

def setup_logging(name):
    """
    Setup and return a named logger using predefined logging settings.
    
    :param name: Name of the logger to retrieve.
    :return: Configured logger instance.
    """
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
