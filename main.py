from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, AudioQuality
import os

# ====== گۆڕاوەکان ======
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# ====== پێکهێنانی بۆت و User Account ======
bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
app = PyTgCalls(user)

# ====== فەرمانی /start ======
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply(
        "🎵 **ڕۆڤان بۆت**\n\n"
        "گۆرانیەک بنێرە بۆ گروپ، دوای کلیک لە **پلەی** پەخش دەکرێت!\n\n"
        "📌 **فەرمانەکان:**\n"
        "/ping - تاقیکردنەوەی کارکردن"
    )

# ====== فەرمانی /ping ======
@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    await message.reply("🏓 پۆنگ! بۆت کاردەکات! ✅")

# ====== وەرگرتنی گۆرانی و ناردنی دوگمەکان ======
@bot.on_message(filters.audio | filters.video | filters.document)
async def audio_handler(client, message: Message):
    chat_id = message.chat.id
    msg_id = message.id
    
    # ناردنی دوگمەی پلەی و وەستان
    await message.reply(
        "🎵 **گۆرانیەک وەرگیرا!**\n\n"
        "▶️ کلیک لەسەر **پلەی** بکە بۆ پەخشکردن\n"
        "⏹ کلیک لەسەر **وەستان** بۆ ڕاگرتنی پەخش",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▶️ پلەی", callback_data=f"play_{chat_id}_{msg_id}"),
                InlineKeyboardButton("⏹ وەستان", callback_data=f"stop_{chat_id}")
            ]
        ])
    )

# ====== کارکردنی دوگمەکان ======
@bot.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    if data.startswith("play_"):
        try:
            # دەرهێنانی IDی پەیام
            parts = data.split("_")
            msg_id = int(parts[2])
            
            await callback_query.answer("⏳ گۆرانی بار دەکرێت...")
            
            # دۆزینەوەی گۆرانی
            msg = await client.get_messages(chat_id, msg_id)
            
            # هەڵگرتنی گۆرانی
            audio_path = None
            if msg.audio:
                audio_path = await msg.download(f"downloads/{msg.audio.file_name}")
                song_name = msg.audio.file_name or "گۆرانی"
            elif msg.video:
                audio_path = await msg.download(f"downloads/{msg.video.file_name}")
                song_name = msg.video.file_name or "گۆرانی"
            elif msg.document:
                audio_path = await msg.download(f"downloads/{msg.document.file_name}")
                song_name = msg.document.file_name or "گۆرانی"
            else:
                await callback_query.message.reply("❌ فایلی گۆرانی نەدۆزرایەوە!")
                return
            
            # چوونە ناو ڤۆیس چات
            await app.join_group_call(
                chat_id,
                AudioPiped(audio_path, audio_parameters=AudioQuality(bitrate=128))
            )
            
            # پەیامی سەرکەوتن بە دوو زمان
            await callback_query.message.reply(
                f"✅ **گۆرانی دەپەخشێت!** 🎵\n"
                f"🎵 **موزیک پخش می‌شود!** 🎵\n\n"
                f"📁 {song_name}\n"
                f"🔊 لە ڤۆیس چاتی گروپدا گوێبگرن!"
            )
            
        except Exception as e:
            await callback_query.message.reply(f"❌ هەڵە: {str(e)[:100]}")
            
    elif data.startswith("stop_"):
        try:
            await app.leave_group_call(chat_id)
            await callback_query.message.reply(
                "⏹ **گۆرانی وەستا!**\n"
                "⏹ **موزیک متوقف شد!**"
            )
            await callback_query.answer("وەستا")
        except Exception as e:
            await callback_query.message.reply(f"❌ هەڵە: {str(e)[:100]}")

# ====== دەستپێکردن ======
print("🚀 بۆت دەستپێدەکات...")

async def main():
    try:
        await bot.start()
        print("✅ بۆت دەستپێکرد")
        await user.start()
        print("✅ User Account دەستپێکرد")
        await app.start()
        print("✅ ڤۆیس چات ئامادەیە!")
        print("🎵 بۆت ئامادەیە بۆ پەخشکردن!")
        await bot.idle()
    except Exception as e:
        print(f"❌ هەڵە: {e}")

import asyncio
asyncio.run(main())
