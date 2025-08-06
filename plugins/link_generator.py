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
        # Send initial prompt message
        prompt = await message.reply_text("Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link")
        
        # First message handling with longer timeout
        first_message = await client.ask(
            text = "Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link", 
            chat_id = message.from_user.id, 
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
            timeout=120
        )
        
        # Process first message
        f_msg_id = await get_message_id(client, first_message)
        if not f_msg_id:
            await first_message.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid\n\nMake sure you're using a link from the correct channel.", quote=True)
            return
        
        # Log successful first message processing
        print(f"Successfully processed first message with ID: {f_msg_id}")
        
        # Second message handling
        await asyncio.sleep(1)  # Small delay for stability
        second_message = await client.ask(
            text = "Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link", 
            chat_id = message.from_user.id, 
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
            timeout=120
        )
        
        # Process second message
        s_msg_id = await get_message_id(client, second_message)
        if not s_msg_id:
            await second_message.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid\n\nMake sure you're using a link from the correct channel.", quote=True)
            return
            
        # Log successful second message processing
        print(f"Successfully processed second message with ID: {s_msg_id}")
        
        # Validate message IDs
        if f_msg_id <= 0 or s_msg_id <= 0:
            await second_message.reply("❌ Invalid message IDs. Please try again with valid messages.", quote=True)
            return
            
        # Generate batch link
        string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
        await second_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)
        
    except asyncio.TimeoutError:
        await message.reply("⏱️ Timeout! Process cancelled. Please try again and respond more quickly.")
    except Exception as e:
        print(f"Error in batch command: {e}")
        await message.reply(f"❌ Error: {str(e)}\n\nPlease try again.")


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Generate a link for a single file"""
    while True:
        try:
            channel_message = await client.ask(
                text = "Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link", 
                chat_id = message.from_user.id, 
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)), 
                timeout=120
            )
        except asyncio.TimeoutError:
            await message.reply("⏱️ Timeout! Process cancelled. Please try again.")
            return
        except Exception as e:
            print(f"Error in genlink command: {e}")
            await message.reply(f"❌ Error: {str(e)}\n\nPlease try again.")
            return
            
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\nThis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote=True)
            continue

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)
