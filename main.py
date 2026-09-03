from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, AudioQuality
import os
import yt_dlp

# ------------------ پێکهێنانی بۆت ------------------
bot = Client("bot", bot_token=BOT_TOKEN)
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
app = PyTgCalls(user)

# ------------------ گۆڕینی URL بۆ ئەودیۆ ------------------
def download_audio(url):
    """گۆڕینی URL بۆ فایلی MP3"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')

# ------------------ دەستپێکردنی پەخش ------------------
async def play_audio(chat_id, audio_path, title="گۆرانی"):
    """پەخشکردنی گۆرانی لە ڤۆیس چات"""
    try:
        await app.join_group_call(
            chat_id,
            AudioPiped(
                audio_path,
                audio_parameters=AudioQuality(bitrate=128)
            )
        )
        return True
    except Exception as e:
        print(f"هەڵە: {e}")
        return False

# ------------------ وەرگرتنی پەیامی گۆرانی ------------------
@bot.on_message(filters.audio | filters.video | filters.document)
async def audio_handler(client, message: Message):
    """کاتێک گۆرانیەک دەنێردرێت"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # دروستکردنی کلیکی پلەی
    await message.reply(
        "🎵 گۆرانیەک وەرگیرا!\n"
        "👆 کلیک لەسەر **پلەی** بکە بۆ پەخشکردن لە ڤۆیس چات",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ پلەی", callback_data=f"play_{message.id}")],
            [InlineKeyboardButton("⏹ وەستان", callback_data="stop")]
        ])
    )

# ------------------ کارکردنی کلیکی پلەی ------------------
@bot.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    if data.startswith("play_"):
        # دۆزینەوەی پەیامی گۆرانی
        msg_id = int(data.split("_")[1])
        msg = await client.get_messages(chat_id, msg_id)
        
        # ناردنی پەیامی چاوەڕوانی
        await callback_query.answer("⏳ گۆرانی بار دەکرێت...")
        
        # هەڵگرتنی گۆرانی
        audio_path = None
        if msg.audio:
            audio_path = await msg.download(f"downloads/{msg.audio.file_name}")
        elif msg.video:
            audio_path = await msg.download(f"downloads/{msg.video.file_name}")
        elif msg.document:
            audio_path = await msg.download(f"downloads/{msg.document.file_name}")
        elif msg.text and "youtube.com" in msg.text:
            # گۆرانی لە یوتیوب
            audio_path = download_audio(msg.text)
        
        if audio_path:
            # چوونە ناو ڤۆیس چات و پەخش
            success = await play_audio(chat_id, audio_path, msg.audio.file_name if msg.audio else "گۆرانی")
            
            if success:
                await callback_query.message.reply(
                    "✅ گۆرانی دەپەخشێت لە ڤۆیس چات!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⏹ وەستان", callback_data="stop")]
                    ])
                )
            else:
                await callback_query.message.reply("❌ نەتوانرا بچێتە ڤۆیس چات!")
        else:
            await callback_query.message.reply("❌ فایلی گۆرانی نەدۆزرایەوە!")
    
    elif data == "stop":
        # وەستاندنی گۆرانی و دەرچوون لە ڤۆیس چات
        await app.leave_group_call(chat_id)
        await callback_query.message.reply("⏹ گۆرانی وەستا!")
        await callback_query.answer("وەستا")

# ------------------ دەستپێکردنی بۆت ------------------
bot.start()
user.start()
app.start()

print("✅ بۆت کاردەکات!")
