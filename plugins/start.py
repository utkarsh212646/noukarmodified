#(©)CodeXBotz

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserBannedInChannel

from bot import Bot
from config import (
    ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, 
    PROTECT_CONTENT, START_PIC, AUTO_DELETE_TIME, AUTO_DELETE_MSG, 
    JOIN_REQUEST_ENABLE, FORCE_SUB_CHANNEL, HEAVY_LOAD_MSG, OWNER_ID
)
from helper_func import (
    subscribed, decode, process_file_request, delete_file
)
from database.database import add_user, del_user, full_userbase, present_user
from datetime import datetime

# Function to send media files to user
async def send_media_and_reply(client, message, messages, temp_msg=None):
    """Send retrieved media files to the user"""
    track_msgs = []
    
    for msg in messages:
        if not msg:
            continue
            
        try:
            if bool(CUSTOM_CAPTION) and bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html, 
                    filename=msg.document.file_name
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None
                
            # Send the file
            if AUTO_DELETE_TIME and AUTO_DELETE_TIME > 0:
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                if copied_msg:
                    track_msgs.append(copied_msg)
            else:
                await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
            
            # Add small delay between files to avoid rate limits
            await asyncio.sleep(0.7)
            
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            # Retry sending after FloodWait
            if AUTO_DELETE_TIME and AUTO_DELETE_TIME > 0:
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                if copied_msg:
                    track_msgs.append(copied_msg)
            else:
                await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
        except Exception as e:
            print(f"Error sending message: {e}")
    
    # Handle auto-deletion
    if track_msgs and AUTO_DELETE_TIME > 0:
        delete_data = await message.reply_text(AUTO_DELETE_MSG.format(time=AUTO_DELETE_TIME))
        asyncio.create_task(delete_file(track_msgs, client, delete_data))
    
    # Clean up temp message
    if temp_msg:
        try:
            await temp_msg.delete()
        except:
            pass

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    # Add user to database if not exists
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    
    text = message.text
    
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            string = await decode(base64_string)
            
            # Process the request directly without queuing
            await process_file_request(client, message, string)
            return
        except Exception as e:
            # Handle invalid links more gracefully
            await message.reply_text("Invalid link or format. Please use a valid file link.", quote=True)
            print(f"Error decoding start command: {e}")
            return
    
    # Handle normal /start command
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("😊 About Me", callback_data="about"),
                InlineKeyboardButton("🔒 Close", callback_data="close")
            ]
        ]
    )
    
    if START_PIC:
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            quote=True
        )
    else:
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    """Handle users who haven't subscribed to required channel"""
    if bool(JOIN_REQUEST_ENABLE):
        invite = await client.create_chat_invite_link(
            chat_id=FORCE_SUB_CHANNEL,
            creates_join_request=True
        )
        ButtonUrl = invite.invite_link
    else:
        ButtonUrl = client.invitelink

    buttons = [
        [
            InlineKeyboardButton(
                "Join Channel",
                url = ButtonUrl)
        ]
    ]

    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    """Admin command to view bot users count"""
    msg = await client.send_message(chat_id=message.chat.id, text="Counting users...")
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(OWNER_ID))
async def send_text(client: Bot, message: Message):
    """Owner command to broadcast message to all users"""
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        start_time = datetime.now()
        
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await broadcast_msg.copy(chat_id)
                    successful += 1
                except:
                    unsuccessful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except Exception as e:
                print(f"Error broadcasting to {chat_id}: {e}")
                unsuccessful += 1
            total += 1
            
            # Show progress every 50 users
            if total % 50 == 0:
                progress = f"""<b>Broadcast Progress 📊</b>
                
<b>Total Users:</b> {len(query)}
<b>Completed:</b> {total} / {len(query)} (<code>{total/len(query)*100:.1f}%</code>)
<b>Success:</b> {successful}
<b>Failed:</b> {unsuccessful + blocked + deleted}

<i>Please wait, broadcasting in progress...</i>"""
                await pls_wait.edit(progress)
        
        time_taken = datetime.now() - start_time
        
        status = f"""<b>✅ Broadcast Completed</b>

<b>📊 Statistics:</b>
• <b>Total Users:</b> <code>{total}</code>
• <b>Successful:</b> <code>{successful}</code> (<code>{successful/total*100:.1f}%</code>)
• <b>Blocked Users:</b> <code>{blocked}</code>
• <b>Deleted Accounts:</b> <code>{deleted}</code>
• <b>Failed Delivery:</b> <code>{unsuccessful}</code>

<b>⏱ Time Taken:</b> <code>{time_taken.seconds}</code> seconds

<i>Note: Blocked and deleted users have been removed from the database</i>"""
        
        return await pls_wait.edit(status)
    else:
        msg = await message.reply("❌ Please reply to a message to broadcast it to users.")
        await asyncio.sleep(5)
        await msg.delete()
