import redis
import hashlib
import json

# Connect to Redis
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

TTL_SECONDS = 900  # 15 minutes

def generate_key(prompt):
    return hashlib.sha256(prompt.encode()).hexdigest()

def get_cache(prompt):
    key = generate_key(prompt)
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def set_cache(prompt, value):
    key = generate_key(prompt)
    redis_client.setex(key, TTL_SECONDS, json.dumps(value))