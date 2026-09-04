import os
import re
import asyncio
import logging

import requests
from dotenv import load_dotenv

from pyrogram import Client, filters, idle
from pyrogram.types import ChatMemberUpdated, Message
from pyrogram.enums import ChatMemberStatus

from music_player import MusicPlayer

# ---------------------------------------------------------------
# ڕێکخستنی سەرەکی
# ---------------------------------------------------------------
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ai-bot")

app = Client("ai_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
music = MusicPlayer(app)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

LINK_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|@\w{4,})", re.IGNORECASE
)

# وشەکانی فەرمانی "لێیدە" بە چەند زمانێک
PLAY_TRIGGERS = {
    "play", "پخش", "پلەی", "لێیدە", "لێی بدە", "بيدە",
    "پخشش کن", "اجرا", "اجراش کن", "شغل", "شغلها", "بزن",
}


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


# ---------------------------------------------------------------
# 1) بەخێرهاتنی ئەندامی نوێ
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

    name = user.first_name or user.username or "بەڕێز"
    mention = f"[{name}](tg://user?id={user.id})"

    text = (
        f"🌹 بەخێربێیت {mention}!\n"
        f"🌹 {mention} خوش آمدید!"
    )
    try:
        await client.send_message(update.chat.id, text)
    except Exception as e:
        log.warning(f"couldn't send welcome message: {e}")


# ---------------------------------------------------------------
# 7) سڕینەوەی پەیامە فەرمییەکانی "هاتنی خەڵک" (join/left service messages)
# ---------------------------------------------------------------
@app.on_message(filters.group & filters.service, group=0)
async def delete_service_messages(client: Client, message: Message):
    try:
        await message.delete()
    except Exception as e:
        log.warning(f"couldn't delete service message: {e}")


# ---------------------------------------------------------------
# 6) سڕینەوەی لینک (لە هەموو ئەندامان، جگە لە ئەدمینەکان)
# ---------------------------------------------------------------
@app.on_message(filters.group & filters.text & ~filters.via_bot, group=1)
async def delete_links(client: Client, message: Message):
    if message.from_user is None or message.from_user.is_bot:
        return

    if await is_admin(client, message.chat.id, message.from_user.id):
        return

    text = message.text or ""
    has_link = bool(LINK_REGEX.search(text)) or bool(
        message.entities and any(e.type.name in ("URL", "TEXT_LINK", "MENTION") for e in message.entities)
    )
    if has_link:
        try:
            await message.delete()
        except Exception as e:
            log.warning(f"couldn't delete link message: {e}")


# ---------------------------------------------------------------
# 5) سڕینەوەی نامەکان (فەرمانی /del بۆ ئەدمین، وەک ڕیپلەی)
# ---------------------------------------------------------------
@app.on_message(filters.command("del") & filters.group)
async def delete_command(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        await message.reply_text("تەنها ئەدمین دەتوانێت ئەمە بکات. / فقط ادمین می‌تواند این کار را انجام دهد.")
        return

    if not message.reply_to_message:
        await message.reply_text("ڕیپلەی ئەو پەیامە بکە کە دەتەوێت بسڕدرێتەوە. / روی پیامی که می‌خواهید حذف شود ریپلای کنید.")
        return

    try:
        await message.reply_to_message.delete()
        await message.delete()
    except Exception as e:
        await message.reply_text(f"هەڵە / خطا: {e}")


# ---------------------------------------------------------------
# 2 و 3) گفتوگۆی زیرەکانە بە هەموو زمانەکان کاتێک ڕیپلەی بۆتەکە یان ناوی دەهێنن
# ---------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a friendly, helpful assistant chatting inside a Telegram group. "
    "Detect the language the user just wrote in and reply in that exact same "
    "language, whatever language it is. Keep answers short, warm, and clear."
)


def ask_ai(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "کلیلی AI ڕێکنەخراوە. / کلید AI تنظیم نشده است."

    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}",
        json={
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": prompt}]}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


@app.on_message(filters.group & filters.text & ~filters.command(["del"]), group=2)
async def reply_when_mentioned(client: Client, message: Message):
    me = await client.get_me()
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == me.id
    )
    is_mentioned = f"@{me.username}".lower() in (message.text or "").lower()

    # ئەگەر ئەمە ڕیپلەیەکی ئۆدیۆیە بۆ لێدانی گۆرانی، بازی بدە (بەشی 4 خۆی هەڵدەگرێت)
    if message.text and message.text.strip().lower() in PLAY_TRIGGERS and message.reply_to_message:
        return

    if not (is_reply_to_bot or is_mentioned):
        return

    prompt = message.text.replace(f"@{me.username}", "").strip()
    if not prompt:
        return

    thinking = await message.reply_text("...")
    try:
        answer = await asyncio.to_thread(ask_ai, prompt)
        await thinking.edit_text(answer[:4000])
    except Exception as e:
        await thinking.edit_text(f"هەڵەیەک ڕوویدا / خطایی رخ داد: {e}")


# ---------------------------------------------------------------
# 4) لێدانی گۆرانی: کەسێک گۆرانیەک دەنێرێت، کەسێکی تر ڕیپلەی
#    دەکاتەوە بە وشەی "play/پخش/پلەی/..." و بۆتەکە لە کۆڵی دەنگیدا لێیدەدات
# ---------------------------------------------------------------
@app.on_message(filters.group & filters.text & filters.reply, group=3)
async def play_replied_audio(client: Client, message: Message):
    trigger = (message.text or "").strip().lower()
    if trigger not in PLAY_TRIGGERS:
        return

    replied = message.reply_to_message
    if not replied or not (replied.audio or replied.voice or replied.document):
        await message.reply_text(
            "ڕیپلەی گۆرانیەک بکە بە وشەی 'play' / 'پخش' / 'پلەی'.\n"
            "به آهنگی ریپلای کنید و بنویسید 'play' یا 'پخش'."
        )
        return

    status = await message.reply_text("🎵 چاوەڕوان بە... / لطفاً صبر کنید...")
    try:
        file_path = await client.download_media(replied, file_name=f"{DOWNLOAD_DIR}/")
        await music.play(message.chat.id, file_path)
        await status.edit_text("▶️ ئێستا لێدەدرێت لە کۆڵی دەنگی / درحال پخش در ویس‌چت.")
    except Exception as e:
        await status.edit_text(f"نەتوانرا لێبدرێت / پخش نشد: {e}")


# ---------------------------------------------------------------
# دەستپێکردن
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.start()
    music.start()
    log.info("Bot started.")
    idle()
