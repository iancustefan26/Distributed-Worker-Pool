import redis

def try_ping_redis(connection):
    try:
        connection.ping()
        return True
    except redis.exceptions.ConnectionError:
        return False