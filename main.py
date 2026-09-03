import os
import re
import time
import asyncio
import logging

from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, Message
from pyrogram.enums import ChatMemberStatus
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp
import google.generativeai as genai

# ---------------------------------------------------------------
# ڕێکخستنی سەرەکی
# ---------------------------------------------------------------
load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    ai_model = None

NEW_MEMBER_WINDOW_SECONDS = int(os.getenv("NEW_MEMBER_WINDOW_SECONDS", "600"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ai-bot")

app = Client("ai_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

new_members: dict[int, dict[int, float]] = {}

LINK_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|@\w{4,})", re.IGNORECASE
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------
# 1) بەخێرهاتنی خەڵک (ئەندامی نوێ)
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
        # 7) سڕینەوەی پاشماوەی هاتنی خەڵک (پەیامی بەخێرهاتن خۆی دوای کەمێک دەسڕێتەوە)
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
# 5 & 6) سڕینەوەی نامە و سڕینەوەی لینک بۆ ئەندامانی نوێ
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

    # ئەگەر ئەندامی نوێ لینک بنووسێت، نامەکەی دەسڕێتەوە
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
# 2 & 3 & 4) وەڵامدانەوە، گفتوگۆ بە زمانە جیاوازەکان، و لێدانی گۆرانی بە ڕیپلەی (پخش / پلەی)
# ---------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful group assistant. "
    "Detect the language of the user's message and reply ONLY in that exact same language. "
    "Keep answers friendly, accurate, and concise."
)

def ask_ai(prompt: str) -> str:
    if not ai_model:
        return "کلیلی AI ڕێکنەخراوە."
    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}"
        response = ai_model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"هەڵە: {e}"


def download_audio(query: str) -> str:
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


@app.on_message(filters.group & filters.text, group=2)
async def handle_group_messages(client: Client, message: Message):
    me = await client.get_me()
    
    is_reply_to_bot = (
        message.reply_to_message 
        and message.reply_to_message.from_user 
        and message.reply_to_message.from_user.id == me.id
    )

    if not is_reply_to_bot:
        return

    text_content = message.text.strip()
    lower_text = text_content.lower()

    # 4) ئەگەر ڕیپلەی وشەی (پخش، پلەی، play, پشک ڤیدیو، هتد) کرابێت بۆ لێدانی گۆرانی
    if any(word in lower_text for word in ["پخش", "پلەی", "play", "لێبدە", "آهنگ"]):
        # دەتوانین دەستەواژەی پخش/پلەی لابەین و ئەوەی ماوە بەدوایدا بگەڕێین یان خودی ناوەکە بەکاربهێنین
        query = re.sub(r'^(پخش|پلەی|play|لێبدە|آهنگ)\s*', '', text_content, flags=IGNORECASE:=re.IGNORECASE).strip()
        if not query:
            query = text_content # ئەگەر تەنها ناوی گۆرانییەکە بوو

        status = await message.reply_text("🎵 گۆرانیەکە داگردەکرێت و دەچێتە ڤۆیس کڵاس... / در حال پخش...")
        try:
            file_path = await asyncio.to_thread(download_audio, query)
            await call_py.play(message.chat.id, MediaStream(file_path))
            await status.edit_text(f"▶️ ئێستا لە ڤۆیس کڵاس لێدەدرێت: {query}")
        except Exception as e:
            await status.edit_text(f"نەتوانرا لە ڤۆیس کڵاس لێبدرێت: {e}")
        return

    # 2 & 3) گفتوگۆ و وەڵامدانەوەی زیرەک بە زمانە جیاوازەکان کاتێک ڕیپلەی بۆت دەکەیت
    thinking = await message.reply_text("...")
    try:
        answer = await asyncio.to_thread(ask_ai, text_content)
        await thinking.edit_text(answer[:4000])
    except Exception as e:
        await thinking.edit_text(f"هەڵەیەک ڕوویدا: {e}")


# ---------------------------------------------------------------
# دەستپێکردنی بۆت
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.start()
    call_py.start()
    log.info("Bot started successfully.")
    from pyrogram import idle
    idle()
