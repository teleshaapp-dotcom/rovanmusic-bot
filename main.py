from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, AudioQuality
import os
import tempfile
from gtts import gTTS
import re

# ====== گۆڕاوەکان ======
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# ====== پێکهێنانی بۆت و User Account ======
bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
app = PyTgCalls(user)

# ====== گۆڕینی دەق بۆ دەنگ ======
async def text_to_voice(text, lang='ku'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        print(f"هەڵە لە TTS: {e}")
        return None

# ====== 1. وەڵامدانەوەی سڵاو ======
GREETINGS_KU = ["سڵاو", "سلاو", "سەلام", "سلام", "سڵاو چۆنی", "سڵاو چونی"]
GREETINGS_FA = ["سلام", "درود", "صبح بخیر", "عصر بخیر"]

@bot.on_message(filters.text & filters.group)
async def greeting_reply(client, message: Message):
    text = message.text.lower()
    user_name = message.from_user.first_name
    
    # کوردی
    for greet in GREETINGS_KU:
        if greet in text:
            await message.reply(
                f"سڵاو {user_name}! بەخێربێیت بۆ گروپ! 🌸\n"
                f"سلام {user_name}! به‌خێر بێیت بۆ گروپ! 🌸"
            )
            return
    
    # فارسی
    for greet in GREETINGS_FA:
        if greet in text:
            await message.reply(
                f"سلام {user_name}! خوش آمدید به گروه! 🌸\n"
                f"سڵاو {user_name}! بەخێربێیت بۆ گروپ! 🌸"
            )
            return

# ====== 2. فەرمانەکان ======
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply(
        "🎵 **ڕۆڤان بۆت**\n\n"
        "من بۆتێکی گۆرانی و دەق بۆ دەنگم!\n\n"
        "📌 **فەرمانەکان:**\n"
        "/tts [دەق] - گۆڕینی دەق بۆ دەنگ\n"
        "/ping - تاقیکردنەوەی کارکردن\n\n"
        "🔊 گۆرانیەک بنێرە، دوای کلیک لە **پلەی** پەخش دەکرێت!"
    )

@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    await message.reply("🏓 پۆنگ! بۆت کاردەکات! ✅")

@bot.on_message(filters.command("tts"))
async def tts_command(client, message: Message):
    text = message.text.replace("/tts", "").strip()
    
    if not text:
        await message.reply("❌ تکایە دەقێک بنووسە! نموونە:\n`/tts سڵاو چۆنی`")
        return
    
    # دەستنیشانکردنی زمان
    lang = 'ku'
    if 'فارسی' in text:
        lang = 'fa'
        text = text.replace('فارسی', '').strip()
    
    wait_msg = await message.reply("⏳ دەق دەگۆڕدرێت بۆ دەنگ...")
    
    audio_file = await text_to_voice(text, lang)
    
    if audio_file:
        await message.reply_audio(
            audio=audio_file,
            title=f"دەق: {text[:30]}...",
            performer="ڕۆڤان بۆت"
        )
        os.remove(audio_file)
        await wait_msg.delete()
        lang_name = 'کوردی' if lang == 'ku' else 'فارسی'
        await message.reply(f"✅ دەق گۆڕدرا بۆ دەنگ! زمان: {lang_name}")
    else:
        await message.reply("❌ هەڵە ڕوویدا!")

# ====== 3. وەرگرتنی گۆرانی و پەخشکردن ======
@bot.on_message(filters.audio | filters.video | filters.document)
async def audio_handler(client, message: Message):
    chat_id = message.chat.id
    msg_id = message.id
    
    # ناردنی دوگمەی پلەی
    await message.reply(
        "🎵 **گۆرانیەک وەرگیرا!**\n\n"
        "▶️ کلیک لەسەر **پلەی** بکە بۆ پەخشکردن لە ڤۆیس چات\n"
        "⏹ کلیک لەسەر **وەستان** بۆ ڕاگرتنی پەخش",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▶️ پلەی", callback_data=f"play_{chat_id}_{msg_id}"),
                InlineKeyboardButton("⏹ وەستان", callback_data=f"stop_{chat_id}")
            ]
        ])
    )

# ====== 4. کارکردنی دوگمەکان ======
@bot.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    
    if data.startswith("play_"):
        try:
            _, _, msg_id = data.split("_")
            msg_id = int(msg_id)
            
            await callback_query.answer("⏳ گۆرانی بار دەکرێت...")
            
            # دۆزینەوەی گۆرانی
            msg = await client.get_messages(chat_id, msg_id)
            
            if msg.audio:
                audio_path = await msg.download(f"downloads/{msg.audio.file_name}")
            elif msg.video:
                audio_path = await msg.download(f"downloads/{msg.video.file_name}")
            elif msg.document:
                audio_path = await msg.download(f"downloads/{msg.document.file_name}")
            else:
                await callback_query.message.reply("❌ فایلی گۆرانی نەدۆزرایەوە!")
                return
            
            # چوونە ناو ڤۆیس چات و پەخش
            await app.join_group_call(
                chat_id,
                AudioPiped(audio_path, audio_parameters=AudioQuality(bitrate=128))
            )
            
            await callback_query.message.reply(
                "✅ **گۆرانی دەپەخشێت!** 🎵\n"
                "لە ڤۆیس چاتی گروپدا گوێبگرن!"
            )
            
        except Exception as e:
            await callback_query.message.reply(f"❌ هەڵە: {str(e)[:100]}")
            
    elif data.startswith("stop_"):
        try:
            await app.leave_group_call(chat_id)
            await callback_query.message.reply("⏹ **گۆرانی وەستا!**")
            await callback_query.answer("وەستا")
        except Exception as e:
            await callback_query.message.reply(f"❌ هەڵە: {str(e)[:100]}")

# ====== 5. دەستپێکردن ======
print("🚀 بۆت دەستپێدەکات...")

async def main():
    try:
        await bot.start()
        print("✅ بۆت دەستپێکرد")
        await user.start()
        print("✅ User Account دەستپێکرد")
        await app.start()
        print("✅ ڤۆیس چات دەستپێکرد")
        print("🎵 بۆت ئامادەیە! ڕاگەیاندنەکە بپشکنە!")
        await bot.idle()
    except Exception as e:
        print(f"❌ هەڵە لە دەستپێکردن: {e}")

import asyncio
asyncio.run(main())
