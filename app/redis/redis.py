import redis

def get_redis_client():
    try:
        client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        client.ping()
        print("Redis connection successful")
        return client
    except redis.ConnectionError:
        print("There is an error in the redis database")
        return None