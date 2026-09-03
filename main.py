from pyrogram import Client, filters
from pyrogram.types import Message
import os

# ====== گۆڕاوەکان ======
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ====== پێکهێنانی بۆت ======
bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# ====== فەرمانی /start ======
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply("✅ بۆت کاردەکات! سڵاو!")

# ====== فەرمانی /ping ======
@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    await message.reply("🏓 پۆنگ! بۆت کاردەکات!")

# ====== هەموو پەیامەکان ======
@bot.on_message(filters.text & filters.group)
async def all_messages(client, message: Message):
    await message.reply(f"پەیامەکەت وەرگیرا: {message.text}")

# ====== دەستپێکردن ======
print("🚀 بۆت دەستپێدەکات...")
print(f"🤖 BOT_TOKEN: {BOT_TOKEN[:10]}...")

try:
    bot.run()
except Exception as e:
    print(f"❌ هەڵە: {e}")
