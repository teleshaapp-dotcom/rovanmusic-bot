import os
from pyrogram import Client, filters
from pyrogram.types import Message
import google.generativeai as genai

# زانیارییەکان
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ڕێکخستنی AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# دروستکردنی بۆت
bot = Client("ai_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# فەرمانی /ai
@bot.on_message(filters.command("ai") & filters.group)
async def ai_command(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("تکایە پرسیارەکەت بنووسە. بۆ نموونە: /ai سڵاو")
        return

    query = " ".join(message.command[1:])
    await message.reply_text("🤖 بەدوای وەڵامدا دەگەڕێم...")

    try:
        response = model.generate_content(query)
        await message.reply_text(f"**🤖 AI:** {response.text}")
    except Exception as e:
        await message.reply_text(f"هەڵەیەک ڕوویدا: {e}")

# دەستپێکردن
bot.run()
