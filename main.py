import os
import re
import time
import asyncio
import logging

import google.generativeai as genai
from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import MessageNotModified

# ---------------------------------------------------------------
# ڕێکخستنی سەرەکی و زانیارییە تایبەتەکان
# ---------------------------------------------------------------
API_ID = 35712521
API_HASH = "b0713b67f41a77cb3271d49f84705d08"
BOT_TOKEN = "8881339041:AAFBpUgTW3f2YD6NvgxIDycDsC11P8Lbb3E"

GEMINI_API_KEY = "AQ.Ab8RN6J8JKVgChkico-Z-JWlLcIgbrjZmXISlv7SyjaasxKKCA"

# ڕێکخستنی کلیلی جیمینای بە کتێبخانەی فەرمی
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

NEW_MEMBER_WINDOW_SECONDS = 600

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ai-bot")

app = Client("rovan_ai_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

new_members: dict[int, dict[int, float]] = {}

LINK_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|@\w{4,})", re.IGNORECASE
)


# ---------------------------------------------------------------
# 1) بەخێرهاتنی ئەندامی نوێ و سڕینەوەی پاشماوەکەی
# ---------------------------------------------------------------
@app.on_chat_member_updated()
async def welcome_new_member(client: Client, update: ChatMemberUpdated):
    if update.new_chat_member is None:
        return
    if update.new_chat_member.status != ChatMemberStatus.MEMBER:
        return
    if update.old_chat_member is not None:
        return

    user = update.new_chat_member.user
    if user.is_bot:
        return

    chat_id = update.chat.id
    new_members.setdefault(chat_id, {})[user.id] = time.time()

    name = user.first_name or user.username or "بەڕێز"
    mention = f"[{name}](tg://user?id={user.id})"

    text = f"بەخێربێیت {mention} بۆ گروپ! 🌹\nخۆشحاڵین بە هاتنت."
    
    try:
        sent_msg = await client.send_message(chat_id, text)
        asyncio.create_task(delete_welcome_later(sent_msg))
    except Exception as e:
        log.warning(f"couldn't send welcome message: {e}")

async def delete_welcome_later(msg: Message):
    await asyncio.sleep(30)
    try:
        await msg.delete()
    except:
        pass


# ---------------------------------------------------------------
# 2) سڕینەوەی لینک بۆ ئەندامانی نوێ لە گروپ
# ---------------------------------------------------------------
@app.on_message(filters.group & ~filters.service, group=1)
async def delete_links_from_new_members(client: Client, message: Message):
    if message.from_user is None or message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    join_time = new_members.get(chat_id, {}).get(user_id)
    if join_time is None:
        return

    if time.time() - join_time > NEW_MEMBER_WINDOW_SECONDS:
        new_members[chat_id].pop(user_id, None)
        return

    text = message.text or message.caption or ""
    has_link = bool(LINK_REGEX.search(text)) or bool(message.entities and any(
        e.type.name in ("URL", "TEXT_LINK", "MENTION") for e in message.entities
    ))

    if has_link:
        try:
            await message.delete()
            mention = f"[{message.from_user.first_name}](tg://user?id={user_id})"
            warn = await client.send_message(
                chat_id,
                f"⚠️ {mention} تکایە لینک مەنێرە تا کاتێک ئەندامی نوێیت."
            )
            await asyncio.sleep(6)
            await warn.delete()
        except Exception as e:
            log.warning(f"couldn't delete message: {e}")


# ---------------------------------------------------------------
# 3) وەڵامدانەوەی AI بە کتێبخانەی فەرمی Google Generative AI
# ---------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Detect the language of the user's message and reply ONLY in that exact same language. "
    "Keep answers friendly, accurate, and concise."
)

def ask_ai(prompt: str) -> str:
    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"هەڵەی پەیوەندی بە AI: {e}"


@app.on_message((filters.private | filters.group) & filters.text & ~filters.command("start"), group=2)
async def handle_ai_messages(client: Client, message: Message):
    if message.from_user and message.from_user.is_bot:
        return

    me = await client.get_me()
    is_private = message.chat.type.name == "PRIVATE"
    
    is_reply_to_bot = (
        message.reply_to_message 
        and message.reply_to_message.from_user 
        and message.reply_to_message.from_user.id == me.id
    )
    
    is_mentioned = f"@{me.username}" in (message.text or "")

    if not is_private and not is_reply_to_bot and not is_mentioned:
        return

    text_content = message.text.strip()
    if not text_content:
        return

    thinking = await message.reply_text("...")
    try:
        answer = await asyncio.to_thread(ask_ai, text_content)
        try:
            await thinking.edit_text(answer[:4000])
        except MessageNotModified:
            pass
    except Exception as e:
        try:
            await thinking.edit_text(f"هەڵە: {e}")
        except MessageNotModified:
            pass


# ---------------------------------------------------------------
# دەستپێکردنی بۆت
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.start()
    log.info("Bot started successfully.")
    from pyrogram import idle
    idle()
