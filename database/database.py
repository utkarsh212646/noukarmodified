#(©) @ThealphaBotz And @Allenspark10 on Telegram
import pymongo
import motor.motor_asyncio
import logging
from config import DB_URI, DB_NAME
from redis_helper import (
    get_cached_user, cache_user, 
    init_redis
)

client = None
database = None
user_data = None
join_requests = None

async def init_mongo():
    global client, database, user_data, join_requests
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            DB_URI,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=60000,
            serverSelectionTimeoutMS=5000
        )
        
        database = client[DB_NAME]
        user_data = database['users']
        join_requests = database['join_requests']
        
        await user_data.create_index('_id')
        await join_requests.create_index([('channel_id', 1), ('user_id', 1)])
        
        logging.info("MongoDB connection established successfully")
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False

async def init_database():
    mongo_success = await init_mongo()
    redis_success = init_redis()
    
    return mongo_success

async def present_user(user_id: int):
    cached_result = get_cached_user(user_id)
    if cached_result is not None:
        return cached_result
    
    found = await user_data.find_one({'_id': user_id})
    result = bool(found)
    
    cache_user(user_id, result)
    return result

async def add_user(user_id: int):
    if not await present_user(user_id):
        try:
            await user_data.insert_one({'_id': user_id})
            cache_user(user_id, True)
        except Exception as e:
            logging.error(f"Error adding user {user_id}: {e}")
    return

async def full_userbase():
    user_ids = []
    try:
        cursor = user_data.find({}, {'_id': 1})
        async for doc in cursor:
            user_ids.append(doc['_id'])
    except Exception as e:
        logging.error(f"Error retrieving users: {e}")
    
    return user_ids

async def del_user(user_id: int):
    try:
        await user_data.delete_one({'_id': user_id})
        cache_user(user_id, False)
    except Exception as e:
        logging.error(f"Error deleting user {user_id}: {e}")
    return

async def add_join_request(channel_id: int, user_id: int):
    try:
        await join_requests.update_one(
            {'channel_id': channel_id, 'user_id': user_id},
            {'$set': {'channel_id': channel_id, 'user_id': user_id}},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error adding join request {channel_id}-{user_id}: {e}")

async def check_join_request_exists(channel_id: int, user_id: int):
    try:
        found = await join_requests.find_one({'channel_id': channel_id, 'user_id': user_id})
        return bool(found)
    except Exception as e:
        logging.error(f"Error checking join request {channel_id}-{user_id}: {e}")
        return False

async def remove_join_request(channel_id: int, user_id: int):
    try:
        await join_requests.delete_one({'channel_id': channel_id, 'user_id': user_id})
    except Exception as e:
        logging.error(f"Error removing join request {channel_id}-{user_id}: {e}")
