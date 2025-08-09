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
    JOIN_REQUEST_ENABLED, FORCE_SUB_CHANNELS, OWNER_ID, HEAVY_LOAD_MSG,
    CHANNEL_ID
)
from helper_func import subscribed, decode, process_file_request, delete_file, get_messages
from database.database import (
    add_user, del_user, full_userbase, present_user,
    add_join_request, remove_join_request, check_join_request,
    clean_old_requests
)

async def send_file(client, message, file_id):
    try:
        if file_id.startswith('http'):
            await message.reply_document(file_id)
        else:
            messages = await get_messages(client, int(file_id))
            for msg in messages:
                await msg.copy(
                    chat_id=message.from_user.id,
                    protect_content=PROTECT_CONTENT
                )
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

async def check_user_auth(client, user_id: int):
    if not FORCE_SUB_CHANNELS:
        return True
    
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                if JOIN_REQUEST_ENABLED:
                    has_request = await check_join_request(user_id, channel_id)
                    if not has_request:
                        return False
                else:
                    return False
        except UserNotParticipant:
            return False
        except Exception as e:
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

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        if not await present_user(user_id):
            await add_user(user_id)
    except Exception as e:
        pass

    if not await check_user_auth(client, user_id):
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
            return

    if len(text) == 6:
        try:
            await send_file(client, message, text)
            return
        except Exception as e:
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
    
    if await check_user_auth(client, user_id):
        string = callback.message.command[1] if len(callback.message.command) > 1 else None
        if string:
            try:
                string = await decode(string)
                await process_file_request(client, callback.message, string)
            except:
                pass
        else:
            await callback.message.delete()
            if START_PIC:
                await callback.message.reply_photo(photo=START_PIC)
            else:
                await callback.message.reply_text(START_MSG)
    else:
        await callback.answer("Join the channels first!", show_alert=True)

@Bot.on_chat_join_request()
async def handle_join_request(client: Client, join_request: ChatJoinRequest):
    if join_request.chat.id in FORCE_SUB_CHANNELS:
        try:
            await add_join_request(join_request.from_user.id, join_request.chat.id)
        except Exception as e:
            pass

@Bot.on_chat_member_updated()
async def handle_member_update(client: Client, chat_member_updated):
    if chat_member_updated.chat.id in FORCE_SUB_CHANNELS:
        if chat_member_updated.new_chat_member and chat_member_updated.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            try:
                await remove_join_request(chat_member_updated.from_user.id, chat_member_updated.chat.id)
            except Exception as e:
                pass

async def cleanup_old_requests():
    while True:
        try:
            await asyncio.sleep(3600)
            await clean_old_requests(24)
        except Exception as e:
            pass

if __name__ == "__main__":
    asyncio.create_task(cleanup_old_requests())
    Bot.run()
