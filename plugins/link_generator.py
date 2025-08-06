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
    waiting_for_first_msg = True
    waiting_for_second_msg = False
    first_msg_id = None
    
    # Use custom handler instead of client.listen()
    @client.on_message(filters.private & filters.user(message.from_user.id))
    async def batch_handler(c, msg):
        nonlocal waiting_for_first_msg, waiting_for_second_msg, first_msg_id
        
        try:
            # Process first message
            if waiting_for_first_msg:
                waiting_for_first_msg = False
                
                # Check if message is valid
                f_msg_id = await get_message_id(client, msg)
                if not f_msg_id:
                    await msg.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid", quote=True)
                    # Ask again for first message
                    waiting_for_first_msg = True
                    return
                
                # Save first msg_id and ask for second message
                first_msg_id = f_msg_id
                waiting_for_second_msg = True
                await message.reply_text("Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link")
                return
                
            # Process second message
            elif waiting_for_second_msg:
                waiting_for_second_msg = False
                
                # Remove handler as we don't need it anymore
                client.remove_handler(batch_handler)
                
                # Check if message is valid
                s_msg_id = await get_message_id(client, msg)
                if not s_msg_id:
                    await msg.reply("❌ Error\n\nThis forwarded post is not from my DB Channel or this Link is not valid", quote=True)
                    return
                
                # Generate batch link
                string = f"get-{first_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
                base64_string = await encode(string)
                link = f"https://t.me/{client.username}?start={base64_string}"
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
                
                await msg.reply_text(
                    f"<b>Here is your link</b>\n\n{link}",
                    quote=True,
                    reply_markup=reply_markup
                )
        except Exception as e:
            print(f"Error in batch handler: {e}")
            await msg.reply_text(f"❌ Error: {str(e)}\n\nPlease try again.")
            client.remove_handler(batch_handler)
    
    # Start the process
    try:
        # Set a timer to automatically remove handler after timeout
        async def timeout_handler():
            await asyncio.sleep(60)  # 60 seconds timeout
            if waiting_for_first_msg or waiting_for_second_msg:
                client.remove_handler(batch_handler)
                await message.reply_text("⏱️ Timeout! Process cancelled.")
        
        asyncio.create_task(timeout_handler())
        
        # Send initial prompt
        await message.reply_text("Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link")
        
    except Exception as e:
        print(f"Error starting batch process: {e}")
        client.remove_handler(batch_handler)
        await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again.")


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Generate a link for a single file"""
    waiting_for_msg = True
    
    # Use custom handler instead of client.listen()
    @client.on_message(filters.private & filters.user(message.from_user.id))
    async def genlink_handler(c, msg):
        nonlocal waiting_for_msg
        
        if waiting_for_msg:
            waiting_for_msg = False
            # Remove handler as we don't need it anymore
            client.remove_handler(genlink_handler)
            
            try:
                msg_id = await get_message_id(client, msg)
                if not msg_id:
                    await msg.reply("❌ Error\n\nThis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote=True)
                    return
                    
                base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
                link = f"https://t.me/{client.username}?start={base64_string}"
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
                
                await msg.reply_text(
                    f"<b>Here is your link</b>\n\n{link}",
                    quote=True,
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Error in genlink handler: {e}")
                await msg.reply_text(f"❌ Error: {str(e)}\n\nPlease try again.")
    
    # Start the process
    try:
        # Set a timer to automatically remove handler after timeout
        async def timeout_handler():
            await asyncio.sleep(60)  # 60 seconds timeout
            if waiting_for_msg:
                client.remove_handler(genlink_handler)
                await message.reply_text("⏱️ Timeout! Process cancelled.")
        
        asyncio.create_task(timeout_handler())
        
        # Send initial prompt
        await message.reply_text("Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link")
        
    except Exception as e:
        print(f"Error starting genlink process: {e}")
        client.remove_handler(genlink_handler)
        await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again.")
