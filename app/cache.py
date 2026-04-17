import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    db=0,
    decode_responses=True
)

def get_cached(key: str):
    val = r.get(key)
    return json.loads(val) if val else None

def set_cached(key: str, value, ttl: int):
    r.setex(key, ttl, json.dumps(value))

def delete_pattern(pattern: str):
    keys = r.keys(pattern)
    if keys:
        r.delete(*keys)