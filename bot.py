
import os
import re
import time
import asyncio
import logging

import requests
from dotenv import load_dotenv

from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, Message
from pyrogram.enums import ChatMemberStatus

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp

# ---------------------------------------------------------------
# ڕێکخستنی سەرەکی
# ---------------------------------------------------------------
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

NEW_MEMBER_WINDOW_SECONDS = int(os.getenv("NEW_MEMBER_WINDOW_SECONDS", "600"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ai-bot")

app = Client("ai_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

# لیستی بەکارهێنەرە نوێیەکان: {chat_id: {user_id: join_timestamp}}
new_members: dict[int, dict[int, float]] = {}

LINK_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|@\w{4,})", re.IGNORECASE
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


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
        return  # گۆڕانکاری ڕۆڵ نەک چوونەژوورەوەی نوێ

    user = update.new_chat_member.user
    if user.is_bot:
        return

    chat_id = update.chat.id
    new_members.setdefault(chat_id, {})[user.id] = time.time()

    name = user.first_name or user.username or "بەڕێز"
    mention = f"[{name}](tg://user?id={user.id})"

    text = (
        f"🇰🇺 بەخێربێیت {mention}! 🌹\n"
        f"کاراکانی گروپ بخوێنەوە و چاوگەڕانی خۆش بێت.\n"
        f"تکایە لینک و ڕیکلام مەنێرە بۆ ماوەیەکی کورت دوای چوونەژوورەوەت.\n\n"
        f"🇮🇷 {mention} خوش آمدید! 🌹\n"
        f"لطفاً قوانین گروه را بخوانید و خوش بگذرد.\n"
        f"لطفاً تا مدتی کوتاه پس از عضویت، لینک یا تبلیغات ارسال نکنید."
    )
    try:
        await client.send_message(chat_id, text)
    except Exception as e:
        log.warning(f"couldn't send welcome message: {e}")


# ---------------------------------------------------------------
# 2) سڕینەوەی لینک/ڕیکلامی ئەندامانی نوێ
# ---------------------------------------------------------------
@app.on_message(filters.group & ~filters.service, group=1)
async def delete_links_from_new_members(client: Client, message: Message):
    if message.from_user is None or message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    join_time = new_members.get(chat_id, {}).get(user_id)
    if join_time is None:
        return  # ئەندامێکی کۆنە، دەستکاری ناکەین

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
                f"⚠️ {mention} تکایە لینک مەنێرە تا کاتێک ئەندامی نوێیت لە گروپەکە.\n"
                f"⚠️ {mention} لطفاً تا زمانی که عضو جدید هستید لینک ارسال نکنید."
            )
            await asyncio.sleep(8)
            await warn.delete()
        except Exception as e:
            log.warning(f"couldn't delete message: {e}")


# ---------------------------------------------------------------
# 3) وەڵامدانەوەی زیرەکانە (AI) کاتێک کەسێک ڕیپلەی بۆت دەکات یان ناوی دێنێت
# ---------------------------------------------------------------
# ڕێنمایی زمان: بۆت تەنها بە کوردی یان فارسی وەڵام دەداتەوە، بەگوێرەی زمانی پرسیارەکە
SYSTEM_PROMPT = (
    "You are a helpful group assistant for a Telegram chat. "
    "The users write in Kurdish (Sorani) or Persian (Farsi) only. "
    "Detect which of these two languages the user's message is written in, "
    "and reply ONLY in that same language — never in English or any other language. "
    "Keep answers short, friendly, and clear."
)


def ask_ai(prompt: str) -> str:
    if AI_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 500,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return "".join(b.get("text", "") for b in data.get("content", []))

    elif AI_PROVIDER == "openai" and OPENAI_API_KEY:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    return "کلیلی AI ڕێکنەخراوە، تکایە لە فایلی .env دایبنێ.\nکلید AI تنظیم نشده، لطفاً در فایل .env آن را وارد کنید."


@app.on_message(filters.group & filters.text & ~filters.command(["play", "skip", "stop", "pause", "resume"]), group=2)
async def reply_when_mentioned(client: Client, message: Message):
    me = await client.get_me()
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == me.id
    )
    is_mentioned = f"@{me.username}".lower() in (message.text or "").lower()

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
        await thinking.edit_text(f"هەڵەیەک ڕوویدا: {e}")


# ---------------------------------------------------------------
# 4) پەخشی گۆرانی بۆ لایڤ/کۆڵی دەنگی گروپ
# ---------------------------------------------------------------
def download_audio(query: str) -> str:
    """گۆرانی داگردەکات لە یوتیوب بە ناو یان بەستەر و ڕێچکەی فایلەکە دەگەڕێنێتەوە."""
    out_path = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
        "quiet": True,
        "default_search": "ytsearch1",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info:
            info = info["entries"][0]
        video_id = info["id"]
    return os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")


@app.on_message(filters.command("play") & filters.group)
async def play_song(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "بەکارهێنان: /play ناوی گۆرانی یان بەستەری یوتیوب\n"
            "کاربرد: /play نام آهنگ یا لینک یوتیوب"
        )
        return

    query = message.text.split(None, 1)[1]
    status = await message.reply_text("🎵 گۆرانیەکە داگردەکرێت... / آهنگ در حال دانلود است...")

    try:
        file_path = await asyncio.to_thread(download_audio, query)
        await call_py.play(message.chat.id, MediaStream(file_path))
        await status.edit_text(f"▶️ ئێستا لێدەدرێت / درحال پخش: {query}")
    except Exception as e:
        await status.edit_text(f"نەتوانرا لێبدرێت / پخش نشد: {e}")


@app.on_message(filters.command("stop") & filters.group)
async def stop_song(client: Client, message: Message):
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply_text("⏹️ ڕاگیرا / متوقف شد.")
    except Exception as e:
        await message.reply_text(f"هەڵە / خطا: {e}")


@app.on_message(filters.command("pause") & filters.group)
async def pause_song(client: Client, message: Message):
    try:
        await call_py.pause(message.chat.id)
        await message.reply_text("⏸️ وەستێنرا / مکث شد.")
    except Exception as e:
        await message.reply_text(f"هەڵە / خطا: {e}")


@app.on_message(filters.command("resume") & filters.group)
async def resume_song(client: Client, message: Message):
    try:
        await call_py.resume(message.chat.id)
        await message.reply_text("▶️ دووبارە دەستیپێکرد / ادامه یافت.")
    except Exception as e:
        await message.reply_text(f"هەڵە / خطا: {e}")


# ---------------------------------------------------------------
# دەستپێکردن
# ---------------------------------------------------------------
async def main():
    await app.start()
    await call_py.start()
    log.info("Bot started.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
