import redis
from setup import redis_connection, logger


def create_consumer(consumer_name):
    try:
        redis_connection.xgroup_createconsumer('tasks', 'worker_group', consumer_name)
        logger.info(f"Consumer '{consumer_name}' created")
    except redis.exceptions.ResponseError as e:
        logger.warning(f"Creating consumer '{consumer_name}' failed : {e}")


def delete_consumer(consumer_name):
    try:
        redis_connection.xgroup_delconsumer('tasks', 'worker_group', consumer_name)
        logger.info(f"Consumer '{consumer_name}' deleted")
    except redis.exceptions.ResponseError as e:
        logger.warning(f"Deleting consumer '{consumer_name}' failed : {e}")