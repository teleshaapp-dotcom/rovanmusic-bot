from pyrogram import Client, filters
from pyrogram.types import Message
import os
import tempfile
from gtts import gTTS

# ====== گۆڕاوەکان ======
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ====== پێکهێنانی بۆت ======
bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

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

# ====== فەرمانی /start ======
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply(
        "🎵 **ڕۆڤان بۆت**\n\n"
        "من بۆتێکی گۆرانی و دەق بۆ دەنگم!\n\n"
        "📌 **فەرمانەکان:**\n"
        "/tts [دەق] - گۆڕینی دەق بۆ دەنگ (کوردی/فارسی)\n"
        "/ping - تاقیکردنەوەی کارکردن"
    )

# ====== فەرمانی /ping ======
@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    await message.reply("🏓 پۆنگ! بۆت کاردەکات! ✅")

# ====== فەرمانی /tts ======
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
        await message.reply(f"✅ دەق گۆڕدرا بۆ دەنگ! زمان: {'کوردی' if lang == 'ku' else 'فارسی'}")
    else:
        await message.reply("❌ هەڵە ڕوویدا! تکایە دووبارە هەوڵبدەرەوە.")

# ====== وەرگرتنی گۆرانی ======
@bot.on_message(filters.audio | filters.video | filters.document)
async def audio_handler(client, message: Message):
    if message.audio:
        await message.reply(f"🎵 گۆرانیەک وەرگیرا!\n📁 ناو: {message.audio.file_name}")
    else:
        await message.reply("📁 فایلێک وەرگیرا!")

# ====== دەستپێکردن ======
print("🚀 بۆت دەستپێدەکات...")
print(f"🤖 ناوی بۆت: {BOT_TOKEN[:15]}...")

try:
    bot.run()
except Exception as e:
    print(f"❌ هەڵە: {e}")
