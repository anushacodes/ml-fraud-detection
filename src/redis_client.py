import redis

def get_redis_client(host: str = 'localhost', port: int = 6379, db: int = 0) -> redis.Redis:
    """
    Returns a connected Redis client.
    """
    return redis.Redis(host=host, port=port, db=db, decode_responses=True)

def get_velocity(client: redis.Redis, user_id: str) -> dict:
    """
    Returns the current counts for a user before scoring.
    """
    v1 = client.get(f"user_1hr_{user_id}")
    v24 = client.get(f"user_24hr_{user_id}")
    return {
        "velocity_1hr": int(v1) if v1 else 0,
        "velocity_24hr": int(v24) if v24 else 0
    }

def update_velocity(client: redis.Redis, user_id: str):
    """
    Increments the counts for a user after a transaction.
    """
    k1 = f"user_1hr_{user_id}"
    k24 = f"user_24hr_{user_id}"
    
    # Use pipeline for atomic operations
    pipe = client.pipeline()
    pipe.incr(k1)
    pipe.incr(k24)
    pipe.execute()
    
    # Set expiration if not already set (or reset it)
    if client.ttl(k1) == -1:
        client.expire(k1, 3600)
    if client.ttl(k24) == -1:
        client.expire(k24, 86400)
