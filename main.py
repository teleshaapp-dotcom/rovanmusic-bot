import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL

# Zanyariyە Rasmiyakani Tawaw
API_ID = 35712521
API_HASH = "b0713b67f41a77cb3271d49f84705d08"
BOT_TOKEN = "8881339041:AAFBpUgTW3f2YD6NvgxIDycDsC11P8Lbb3E"

app = Client(
    "rovanmusic",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("🎵 سڵاو غازی گیان! بۆتی مۆزیک لەسەر ڕێپۆزیتۆری نوێ بە سەرکەوتوویی ئامادە شد و کار دەکات.")

print("Bot is starting...")
app.run()
