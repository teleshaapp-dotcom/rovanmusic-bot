import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL

# زانیارییە سەرەتاییەکان بۆ تاقیکردنەوە و کارپێکردنی بۆت
API_ID = 6  # دەتوانیت لە My.telegram.org وەریبگریت
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
BOT_TOKEN = "لێرەدا تۆکنی بۆتەکەت لە تەلەگرام دابنە"

app = Client(
    "rovanmusic",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("🎵 سڵاو! بۆتی مۆزیک ئامادەیە و کار دەکات.")

print("Bot is starting...")
app.run()

