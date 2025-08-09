#(©)CodeXBotz

import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

#Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "7982087834:AAEhY2Eu_led_0BN8vxkmcEOKN1m39IItgA")

#Your API ID from my.telegram.org
APP_ID = int(os.environ.get("APP_ID", "29466135"))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "232617be1aee79aba33e24f26d3e1610")

#Your db channel Id
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002500248330"))

#OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", "7299672444"))

#Port
PORT = os.environ.get("PORT", "8080")

#Database 
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://eramugcar:eRqRTpo6fBjhqccC@cluster0.vyoccaj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "cluster0")

# Redis configuration for caching and rate limiting
REDIS_URI = os.environ.get("REDIS_URI", "redis://default:bSisSsK3F3PkSDyca5xcG0GO4MAyUjxT@redis-12733.c263.us-east-1-2.ec2.redns.redis-cloud.com:12733")  # Format: redis://username:password@host:port/db_number
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
REDIS_PREFIX = os.environ.get("REDIS_PREFIX", "filebot:")

# Performance optimization settings
MAX_CONCURRENT_REQUESTS = int(os.environ.get("MAX_CONCURRENT_REQUESTS", "100"))
USER_REQUEST_COOLDOWN = float(os.environ.get("USER_REQUEST_COOLDOWN", "1"))  # Seconds between requests from same user
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10"))  # Number of files to process at once

#force sub channel id, if you want enable force sub
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "-1002759209644"))
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "6"))  # Increased default worker count

#start message
START_PIC = os.environ.get("START_PIC","")
START_MSG = os.environ.get("START_MESSAGE", "Hello {first}\n\nI can store private files in Specified Channel and other users can access it from special link.")
try:
    ADMINS=[]
    for x in (os.environ.get("ADMINS", "7299672444").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

#Force sub message 
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {first}\n\n<b>You need to join in my Channel/Group to use me\n\nKindly Please join Channel</b>")

#set your Custom Caption here, Keep None for Disable Custom Caption
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

#set True if you want to prevent users from forwarding files from bot
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "True") == "True" else False

# Join Req Config

JOIN_REQUEST_ENABLED = os.environ.get("JOIN_REQUEST_ENABLED", "True") == "True"
FORCE_SUB_CHANNELS = [int(x) for x in os.environ.get("FORCE_SUB_CHANNELS", "-1002759209644").split(",") if x]

REQUEST_TRACKING_COLLECTION = os.environ.get("REQUEST_TRACKING_COLLECTION", "join_requests")

REQUEST_CLEANUP_INTERVAL = int(os.environ.get("REQUEST_CLEANUP_INTERVAL", "3600"))
REQUEST_EXPIRY_HOURS = int(os.environ.get("REQUEST_EXPIRY_HOURS", "24"))

INVITE_LINK_CACHE_TIME = int(os.environ.get("INVITE_LINK_CACHE_TIME", "3600"))
MAX_INVITE_LINKS_PER_CHANNEL = int(os.environ.get("MAX_INVITE_LINKS_PER_CHANNEL", "100"))

MAX_CONCURRENT_REQUESTS = int(os.environ.get("MAX_CONCURRENT_REQUESTS", "100"))
USER_REQUEST_COOLDOWN = float(os.environ.get("USER_REQUEST_COOLDOWN", "1"))

# Auto delete time in seconds.
AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", "1200"))
AUTO_DELETE_MSG = os.environ.get("AUTO_DELETE_MSG", "This file will be automatically deleted in {time} seconds. Please ensure you have saved any necessary content before this time.")
AUTO_DEL_SUCCESS_MSG = os.environ.get("AUTO_DEL_SUCCESS_MSG", "Your file has been successfully deleted. Thank you for using our service. ✅")

#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "❌Don't send me messages directly I'm only File Share bot!"

# Under heavy load message
HEAVY_LOAD_MSG = os.environ.get("HEAVY_LOAD_MSG", "Bot is experiencing heavy load right now. Your request is in queue and will be processed shortly. Please be patient.")

ADMINS.append(OWNER_ID)
ADMINS.append(1250450587)

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
