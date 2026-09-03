import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# زانیارییەکان لە ڕێڵوەی (Environment Variables) وەردەگرین
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# دروستکردنی بۆت و یوزەر
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

# دروستکردنی پەیوەندی دەنگی
call = PyTgCalls(user)

# ====================== هەندێک وەڵامی سادە ======================
GREETINGS_KU = ["سڵاو! چۆنی؟ 😊", "بەخێربێیت بۆ گروپ! 🌹"]
GREETINGS_FA = ["سلام! چطوری؟ 😊", "خوش آمدید! 🌹"]

HOW_KU = "من باشم! تۆ چۆنی؟ 😊"
HOW_FA = "من خوبم! تو چطوری؟ 😊"

# ====================== فەرمانەکان ======================
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    await message.reply_text("من بۆتێکی مۆسیقام! 🎵\nفەرمانی /play بەکاربهێنە بۆ لێدانی گۆرانی.")

@bot.on_message(filters.command("play"))
async def play_command(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("تکایە ناوی گۆرانییەکە بنووسە. بۆ نموونە: /play Sia Unstoppable")
        return

    query = " ".join(message.command[1:])
    chat_id = message.chat.id

    await message.reply_text(f"🔍 بەدوای گۆرانی {query} دەگەڕێم...")

    # پەیوەندی بە گروپەوە دەکەین
    try:
        await call.join_group_call(
            chat_id,
            MediaStream(
                f"https://www.youtube.com/results?search_query={query}",
                audio_parameters=MediaStream.AudioParameters(
                    bitrate=48000,
                ),
            ),
        )
        await message.reply_text(f"🎵 ئێستا گۆرانی {query} لێدەدرێت!")
    except Exception as e:
        await message.reply_text(f"هەڵەیەک ڕوویدا: {e}")

# ====================== وەڵامدانەوەی سادە ======================
@bot.on_message(filters.text & filters.group)
async def reply_handler(client, message: Message):
    text = message.text.lower() if message.text else ""
    user_name = message.from_user.first_name if message.from_user else "بەکارهێنەر"

    if any(word in text for word in ["چۆنی", "چطوری"]):
        await message.reply_text(HOW_KU)
    elif any(word in text for word in ["سڵاو", "سلام"]):
        await message.reply_text(GREETINGS_KU[0])

# ====================== دەستپێکردن ======================
async def main():
    # دەستپێکردنی یوزەر پێش بۆت
    await user.start()
    await call.start()
    await bot.start()
    print("✅ بۆتەکە بە سەرکەوتوویی کار دەکات!")
    await pyrogram.idle()

if __name__ == "__main__":
    import asyncio
    import pyrogram
    asyncio.run(main())
