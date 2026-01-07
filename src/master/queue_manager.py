import redis
from setup import redis_connection, logger

def create_consumer(consumer_name):
    """
    Create a consumer within an existing Redis consumer group.

    This function registers a new consumer under the specified Redis stream and
    consumer group. If the consumer already exists or the operation fails, a
    warning is logged instead of raising an exception.

    :param consumer_name: Name of the consumer to create.
    """

    try:
        redis_connection.xgroup_createconsumer('tasks', 'worker_group', consumer_name)
        logger.info(f"Consumer '{consumer_name}' created")
    except redis.exceptions.ResponseError as e:
        logger.warning(f"Creating consumer '{consumer_name}' failed : {e}")


def delete_consumer(consumer_name):
    """
    Delete a consumer from an existing Redis consumer group.

    This function removes a consumer from the specified Redis stream and consumer
    group. If the consumer does not exist or the operation fails, a warning is
    logged instead of raising an exception.

    :param consumer_name: Name of the consumer to delete.
    """

    try:
        redis_connection.xgroup_delconsumer('tasks', 'worker_group', consumer_name)
        logger.info(f"Consumer '{consumer_name}' deleted")
    except redis.exceptions.ResponseError as e:
        logger.warning(f"Deleting consumer '{consumer_name}' failed : {e}")