#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import re
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Generate a batch link for multiple files"""
    try:
        # First message
        first_prompt = await message.reply_text("Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link")
        
        # Wait for first message response
        first_response = await client.listen(message.chat.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        
        # Process first message
        f_msg_id = await get_message_id(client, first_response)
        if not f_msg_id:
            await first_response.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid", quote=True)
            await client.listen.cancel_listener()
            return
        
        # Second message
        second_prompt = await message.reply_text("Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link")
        
        # Wait for second message response
        second_response = await client.listen(message.chat.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        
        # Process second message
        s_msg_id = await get_message_id(client, second_response)
        if not s_msg_id:
            await second_response.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid", quote=True)
            await client.listen.cancel_listener()
            return
        
        # Generate batch link
        string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
        
        await second_response.reply_text(
            f"<b>Here is your link</b>\n\n{link}",
            quote=True,
            reply_markup=reply_markup
        )
        
    except asyncio.TimeoutError:
        await message.reply_text("⏱️ Timeout! Process cancelled.")
    except Exception as e:
        print(f"Error in batch command: {e}")
        await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again.")
    finally:
        # Always ensure listener is canceled
        try:
            await client.listen.cancel_listener()
        except:
            pass

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Generate a link for a single file"""
    try:
        await message.reply_text("Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link")
        
        # Wait for message response
        response = await client.listen(message.chat.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        
        msg_id = await get_message_id(client, response)
        if not msg_id:
            await response.reply("❌ Error\n\nThis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote=True)
            await client.listen.cancel_listener()
            return
            
        base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
        
        await response.reply_text(
            f"<b>Here is your link</b>\n\n{link}",
            quote=True,
            reply_markup=reply_markup
        )
        
    except asyncio.TimeoutError:
        await message.reply_text("⏱️ Timeout! Process cancelled.")
    except Exception as e:
        print(f"Error in genlink command: {e}")
        await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again.")
    finally:
        # Always ensure listener is canceled
        try:
            await client.listen.cancel_listener()
        except:
            pass
