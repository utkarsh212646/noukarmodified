#(©)Codexbotz

import base64
import re
import asyncio
import logging
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNEL, ADMINS, AUTO_DELETE_TIME, AUTO_DEL_SUCCESS_MSG
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

# Remove the rate limiting mechanism
# Remove task semaphore that was limiting concurrent operations

async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNEL:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
    except UserNotParticipant:
        return False

    if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
        return False
    else:
        return True

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, message_ids):
    """Fetch messages directly without caching delays"""
    messages = []
    
    try:
        # Get all messages in one API call if possible
        batch_msgs = await client.get_messages(
            chat_id=client.db_channel.id,
            message_ids=message_ids
        )
        
        if isinstance(batch_msgs, list):
            messages.extend(batch_msgs)
        else:
            messages.append(batch_msgs)
            
    except FloodWait as e:
        logging.warning(f"FloodWait in get_messages: {e.value}s")
        await asyncio.sleep(e.value + 1)
        # Try again after waiting
        return await get_messages(client, message_ids)
    except Exception as e:
        logging.error(f"Error fetching messages: {e}")
    
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

async def delete_file(messages, client, process):
    try:
        await asyncio.sleep(AUTO_DELETE_TIME)
        for msg in messages:
            try:
                await client.delete_messages(chat_id=msg.chat.id, message_ids=[msg.id])
            except Exception as e:
                logging.error(f"Error deleting message {msg.id}: {e}")

        await process.edit_text(AUTO_DEL_SUCCESS_MSG)
    except Exception as e:
        logging.error(f"Error in delete_file: {e}")

async def process_file_request(client, message, string):
    """Process file request immediately without queue or rate limiting"""
    user_id = message.from_user.id
    
    try:
        # Parse the request
        argument = string.split("-")
        temp_msg = await message.reply_text("Getting your file(s)...")
        
        # Extract message IDs
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                await temp_msg.edit("Invalid link")
                return
                
            if start <= end:
                ids = list(range(start, end + 1))
            else:
                ids = list(range(start, start - end - 1, -1))
                
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                await temp_msg.edit("Invalid link")
                return
        else:
            await temp_msg.edit("Invalid link")
            return
        
        # Get messages directly
        messages = await get_messages(client, ids)
        
        if not messages:
            await temp_msg.edit("No files found.")
            return
            
        # Process retrieved messages immediately
        from plugins.start import send_media_and_reply
        await send_media_and_reply(client, message, messages, temp_msg)
        
    except Exception as e:
        logging.error(f"Error processing file request: {e}")
        try:
            await message.reply_text("An error occurred while processing your request.")
        except:
            pass
            
# Create filter
subscribed = filters.create(is_subscribed)
