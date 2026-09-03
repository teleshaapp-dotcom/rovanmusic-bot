from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, AudioQuality
import os
import tempfile
from gtts import gTTS

# ====== گۆڕاوەکان ======
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# ====== پێکهێنانی بۆت ======
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
        print(f"هەڵە: {e}")
        return None

# ====== فەرمانەکان ======
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply(
        "🎵 **ڕۆڤان بۆت**\n\n"
        "من بۆتێکی گۆرانی و دەق بۆ دەنگم!\n\n"
        "📌 **فەرمانەکان:**\n"
        "/tts [دەق] - گۆڕینی دەق بۆ دەنگ\n"
        "/ping - تاقیکردنەوە\n\n"
        "🔊 گۆرانیەک بنێرە بۆ پەخشکردن لە ڤۆیس چات!"
    )

@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    await message.reply("🏓 پۆنگ! بۆت کاردەکات!")

@bot.on_message(filters.command("tts"))
async def tts_command(client, message: Message):
    text = message.text.replace("/tts", "").strip()
    
    if not text:
        await message.reply("❌ تکایە دەقێک بنووسە! نموونە:\n`/tts سڵاو چۆنی`")
        return
    
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
        await message.reply(f"✅ دەق گۆڕدرا بۆ دەنگ! زمان: {'کوردی' if lang == 'ku' else 'فارسی'}")
    else:
        await message.reply("❌ هەڵە ڕوویدا!")

@bot.on_message(filters.audio | filters.video | filters.document)
async def audio_handler(client, message: Message):
    await message.reply(
        "🎵 گۆرانیەک وەرگیرا!\n"
        "▶️ کلیک لەسەر **پلەی** بکە بۆ پەخشکردن",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ پلەی", callback_data=f"play_{message.id}")],
            [InlineKeyboardButton("⏹ وەستان", callback_data="stop")]
        ])
    )

@bot.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    if data.startswith("play_"):
        await callback_query.answer("⏳ گۆرانی بار دەکرێت...")
        msg_id = int(data.split("_")[1])
        msg = await client.get_messages(chat_id, msg_id)
        
        if msg.audio:
            audio_path = await msg.download(f"downloads/{msg.audio.file_name}")
            await app.join_group_call(chat_id, AudioPiped(audio_path, AudioQuality(bitrate=128)))
            await callback_query.message.reply("✅ گۆرانی دەپەخشێت!")
        else:
            await callback_query.message.reply("❌ فایلی گۆرانی نەدۆزرایەوە!")
    
    elif data == "stop":
        await app.leave_group_call(chat_id)
        await callback_query.message.reply("⏹ گۆرانی وەستا!")
        await callback_query.answer("وەستا")

# ====== دەستپێکردن ======
print("🚀 بۆت دەستپێدەکات...")

async def main():
    await bot.start()
    await user.start()
    await app.start()
    print("✅ بۆت بە سەرکەوتوویی کاردەکات!")
    await bot.idle()

import asyncio
asyncio.run(main())
