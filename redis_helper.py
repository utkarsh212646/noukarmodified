import redis
import json
import logging
from config import REDIS_URI, REDIS_PASSWORD, REDIS_PREFIX
import time

# Initialize Redis client
redis_client = None

def init_redis():
    global redis_client
    try:
        if REDIS_URI:
            # Use provided Redis URI
            redis_client = redis.from_url(REDIS_URI)
        elif REDIS_PASSWORD:
            # Use provided Redis password with default host/port
            redis_client = redis.Redis(host='localhost', port=6379, password=REDIS_PASSWORD, decode_responses=True)
        else:
            # Use default local Redis without password
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
        redis_client.ping()  # Test connection
        logging.info("Redis connection established successfully")
        return True
    except redis.ConnectionError as e:
        logging.error(f"Redis connection error: {e}")
        redis_client = None
        return False
    except Exception as e:
        logging.error(f"Redis initialization error: {e}")
        redis_client = None
        return False

# Key generation helpers with prefix
def get_user_key(user_id):
    return f"{REDIS_PREFIX}user:{user_id}"

def get_file_key(file_id):
    return f"{REDIS_PREFIX}file:{file_id}"

# Cache user data functions
def cache_user(user_id, exists=True, ttl=7200):
    """Cache user existence in Redis"""
    if not redis_client:
        return False
        
    try:
        key = get_user_key(user_id)
        redis_client.setex(key, ttl, "1" if exists else "0")
        return True
    except Exception as e:
        logging.error(f"User cache error: {e}")
        return False

def get_cached_user(user_id):
    """Check if user exists in Redis cache"""
    if not redis_client:
        return None
        
    try:
        key = get_user_key(user_id)
        data = redis_client.get(key)
        if data is not None:
            return data == "1"
        return None
    except Exception as e:
        logging.error(f"Get user cache error: {e}")
        return None

# Stats tracking functions
def increment_request_counter():
    """Increment total request counter"""
    if not redis_client:
        return
        
    try:
        stats_key = f"{REDIS_PREFIX}stats"
        redis_client.hincrby(stats_key, "total_requests", 1)
    except Exception:
        pass

def increment_processed_counter():
    """Increment processed request counter"""
    if not redis_client:
        return
        
    try:
        stats_key = f"{REDIS_PREFIX}stats"
        redis_client.hincrby(stats_key, "processed_requests", 1)
    except Exception:
        pass

def get_stats():
    """Get bot statistics"""
    if not redis_client:
        return {"total_requests": 0, "processed_requests": 0}
        
    try:
        stats_key = f"{REDIS_PREFIX}stats"
        stats = redis_client.hgetall(stats_key)
        return {
            "total_requests": int(stats.get("total_requests", 0)),
            "processed_requests": int(stats.get("processed_requests", 0))
        }
    except Exception:
        return {"total_requests": 0, "processed_requests": 0}
