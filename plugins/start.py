# © @TheAlphaBotz for this code 
# @TheAlphaBotz [2021-2025]
# © Utkarsh dubey [github.com/utkarshdubey2008] 
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatJoinRequest
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserBannedInChannel, UserNotParticipant
import datetime
import asyncio

from bot import Bot
from config import (
    ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, 
    PROTECT_CONTENT, START_PIC, AUTO_DELETE_TIME, AUTO_DELETE_MSG,
    JOIN_REQUEST_ENABLED, FORCE_SUB_CHANNELS, OWNER_ID, HEAVY_LOAD_MSG
)
from helper_func import subscribed, decode, process_file_request, delete_file
from database.database import (
    add_user, del_user, full_userbase, present_user,
    add_join_request, remove_join_request, check_join_request,
    clean_old_requests
)

async def send_media_and_reply(client, message, messages, temp_msg=None):
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

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None
                
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
            
            await asyncio.sleep(0.7)
            
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
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
    
    if track_msgs and AUTO_DELETE_TIME > 0:
        delete_data = await message.reply_text(AUTO_DELETE_MSG.format(time=AUTO_DELETE_TIME))
        asyncio.create_task(delete_file(track_msgs, client, delete_data))
    
    if temp_msg:
        try:
            await temp_msg.delete()
        except:
            pass

async def check_subscription(client, user_id):
    if not FORCE_SUB_CHANNELS:
        return True
        
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                if JOIN_REQUEST_ENABLED and await check_join_request(user_id, channel_id):
                    continue
                return False
        except UserNotParticipant:
            return False
        except Exception as e:
            print(f"Error checking subscription: {e}")
            continue
    return True

async def generate_invite_links(client, user_id):
    buttons = []
    try:
        for channel_id in FORCE_SUB_CHANNELS:
            chat = await client.get_chat(channel_id)
            
            if JOIN_REQUEST_ENABLED:
                try:
                    invite = await client.create_chat_invite_link(
                        chat_id=channel_id,
                        creates_join_request=True,
                        name=f"User_{user_id}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                    )
                    link = invite.invite_link
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    continue
            else:
                link = f"https://t.me/{chat.username}" if chat.username else chat.invite_link
            
            if link:
                buttons.append([InlineKeyboardButton(f"📢 Join {chat.title}", url=link)])
    except Exception as e:
        print(f"Error generating invite links: {e}")
    
    if buttons:
        buttons.append([InlineKeyboardButton("🔄 Check Subscription", callback_data=f"checksub_{user_id}")])
    
    return InlineKeyboardMarkup(buttons) if buttons else None

@Bot.on_chat_join_request()
async def handle_join_request(client: Client, join_request: ChatJoinRequest):
    if join_request.chat.id in FORCE_SUB_CHANNELS:
        try:
            await add_join_request(join_request.from_user.id, join_request.chat.id)
        except Exception as e:
            print(f"Error handling join request: {e}")

@Bot.on_chat_member_updated()
async def handle_member_update(client: Client, member_updated):
    if member_updated.chat.id in FORCE_SUB_CHANNELS:
        if member_updated.new_chat_member and member_updated.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            try:
                await remove_join_request(member_updated.from_user.id, member_updated.chat.id)
            except Exception as e:
                print(f"Error handling member update: {e}")

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        if not await present_user(user_id):
            await add_user(user_id)
    except Exception as e:
        print(f"Error adding user: {e}")

    if not await check_subscription(client, user_id):
        buttons = await generate_invite_links(client, user_id)
        if buttons:
            await message.reply(
                text=FORCE_MSG.format(
                    first=message.from_user.first_name,
                    last=message.from_user.last_name,
                    username=None if not message.from_user.username else '@' + message.from_user.username,
                    mention=message.from_user.mention,
                    id=user_id
                ),
                reply_markup=buttons,
                quote=True,
                disable_web_page_preview=True
            )
            return

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            string = await decode(base64_string)
            await process_file_request(client, message, string)
            return
        except Exception as e:
            await message.reply_text("Invalid link or format. Please use a valid file link.", quote=True)
            return

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("😊 About Me", callback_data="about"),
        InlineKeyboardButton("🔒 Close", callback_data="close")
    ]])
    
    if START_PIC:
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=user_id
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
                id=user_id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )

@Bot.on_callback_query(filters.regex("^checksub_"))
async def check_subscription_callback(client: Client, callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    if callback.from_user.id != user_id:
        return await callback.answer("This button is not for you!", show_alert=True)
    
    if await check_subscription(client, user_id):
        await callback.message.edit("✅ Thank you for subscribing! Send /start to use the bot.")
    else:
        await callback.answer("❌ You haven't joined all channels yet!", show_alert=True)

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text="Counting users...")
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(OWNER_ID))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        start_time = datetime.datetime.now()
        
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
            
            if total % 50 == 0:
                progress = f"""<b>Broadcast Progress 📊</b>
<b>Total Users:</b> {len(query)}
<b>Completed:</b> {total} / {len(query)} (<code>{total/len(query)*100:.1f}%</code>)
<b>Success:</b> {successful}
<b>Failed:</b> {unsuccessful + blocked + deleted}

<i>Please wait, broadcasting in progress...</i>"""
                await pls_wait.edit(progress)
        
        time_taken = datetime.datetime.now() - start_time
        
        status = f"""<b>✅ Broadcast Completed</b>

<b>📊 Statistics:</b>
• <b>Total Users:</b> <code>{total}</code>
• <b>Successful:</b> <code>{successful}</code> (<code>{successful/total*100:.1f}%</code>)
• <b>Blocked Users:</b> <code>{blocked}</code>
• <b>Deleted Accounts:</b> <code>{deleted}</code>
• <b>Failed Delivery:</b> <code>{unsuccessful}</code>

<b>⏱ Time Taken:</b> <code>{time_taken.seconds}</code> seconds"""
        
        return await pls_wait.edit(status)
    else:
        msg = await message.reply("❌ Please reply to a message to broadcast it to users.")
        await asyncio.sleep(5)
        await msg.delete()

async def cleanup_old_requests():
    while True:
        try:
            await asyncio.sleep(3600)
            await clean_old_requests(24)
        except Exception as e:
            print(f"Error in cleanup: {e}")

if __name__ == "__main__":
    asyncio.create_task(cleanup_old_requests())
    Bot.run()
