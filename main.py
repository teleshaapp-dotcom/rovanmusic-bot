import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import google.generativeai as genai
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# زانیارییەکان
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ڕێکخستنی AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# دروستکردنی بۆت و یوزەر
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
call = PyTgCalls(user)

# وەڵامە ئامادەکان
GREETING_KU = "سڵاو! چۆنی؟ 😊"
GREETING_FA = "سلام! چطوری؟ 😊"
HOW_KU = "من باشم! تۆ چۆنی؟ 😊"
HOW_FA = "من خوبم! تو چطوری؟ 😊"

# دەستپێکردنی بۆت
@bot.on_startup()
async def startup():
    await user.start()
    await call.start()
    print("✅ بۆتەکە بە سەرکەوتوویی کاردەکات!")

# فەرمانی /play بۆ گۆرانی
@bot.on_message(filters.command("play") & filters.group)
async def play_command(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("تکایە ناوی گۆرانییەکە بنووسە. بۆ نموونە: /play Sia Unstoppable")
        return

    query = " ".join(message.command[1:])
    chat_id = message.chat.id

    await message.reply_text(f"🔍 بەدوای گۆرانی {query} دەگەڕێم...")

    try:
        await call.join_group_call(
            chat_id,
            MediaStream(
                f"https://www.youtube.com/results?search_query={query}",
                audio_parameters=MediaStream.AudioParameters(bitrate=48000),
            ),
        )
        await message.reply_text(f"🎵 ئێستا گۆرانی {query} لێدەدرێت!")
    except Exception as e:
        await message.reply_text(f"هەڵەیەک ڕوویدا: {e}")

# وەڵامدانەوەی ئامادە
@bot.on_message(filters.text & filters.group & ~filters.bot)
async def reply_ready(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user.id == (await client.get_me()).id:
        query = message.text
        await message.reply_text("🤖 بەدوای وەڵامدا دەگەڕێم...")
        try:
            response = model.generate_content(query)
            await message.reply_text(f"**🤖 AI:** {response.text}")
        except Exception as e:
            await message.reply_text(f"هەڵەیەک ڕوویدا: {e}")
    else:
        text = message.text.lower()
        if any(word in text for word in ["سڵاو", "سلام"]):
            await message.reply_text(GREETING_KU)
        elif "چۆنی" in text:
            await message.reply_text(HOW_KU)
        elif "چطوری" in text:
            await message.reply_text(HOW_FA)
        elif "سلام" in text:
            await message.reply_text(GREETING_FA)

# وەڵامدانەوەی AI بەبێ فەرمان
@bot.on_message(filters.text & filters.private & ~filters.bot)
async def ai_private(client, message: Message):
    query = message.text
    await message.reply_text("🤖 بەدوای وەڵامدا دەگەڕێم...")
    try:
        response = model.generate_content(query)
        await message.reply_text(f"**🤖 AI:** {response.text}")
    except Exception as e:
        await message.reply_text(f"هەڵەیەک ڕوویدا: {e}")
