from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, AudioQuality
import os
import random
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

# ====== داتاکانی وەڵامدانەوە ======

# وەڵامی سڵاو (کوردی)
GREETINGS_KU = [
    "سڵاو {}! بەخێربێیت بۆ گروپ! 🌸 چۆنی؟",
    "سڵاو {}! خۆشحاڵین بە بینینی تۆ! 💫",
    "سڵاو {}! بەخێربێیت، ئەم گروپە بۆ تۆ خۆشە! 🌺",
    "سڵاو {}! چۆنی؟ هیوادارم ڕۆژێکی خۆش بێت! ☀️",
    "سڵاو {}! بەخێربێیت، ئەمە شوێنی خۆتە! 🏠"
]

# وەڵامی سڵاو (فارسی)
GREETINGS_FA = [
    "سلام {}! خوش آمدید به گروه! 🌸 حالت چطوره؟",
    "سلام {}! خوشحالیم که اینجایی! 💫",
    "سلام {}! خوش آمدید، این گروه برای شما زیباست! 🌺",
    "سلام {}! چطوری؟ امیدوارم روز خوبی داشته باشی! ☀️",
    "سلام {}! خوش آمدید، اینجا جای شماست! 🏠"
]

# وەڵامی پرسیاری چۆنی (کوردی)
HOW_KU = [
    "من باشم، سوپاس {}! تۆ چۆنی؟ 😊",
    "زۆر باشم {}! بە سوپاس! تۆ چۆنی؟ 🌸",
    "خۆش و خۆشم {}! تۆ چۆنی؟ 💫"
]

# وەڵامی پرسیاری چۆنی (فارسی)
HOW_FA = [
    "من خوبم، ممنون {}! تو چطوری؟ 😊",
    "خیلی خوبم {}! ممنون! تو چطوری؟ 🌸",
    "خوش و خرم {}! تو چطوری؟ 💫"
]

# وەڵامی سوپاس (کوردی)
THANK_KU = [
    "بەخێربێیت {}! ☺️",
    "شایەنی سوپاس نەبوو {}! 🌸",
    "هیچ شتێک نییە {}! 😊"
]

# وەڵامی سوپاس (فارسی)
THANK_FA = [
    "خواهش می‌کنم {}! ☺️",
    "قابل شما رو نداره {}! 🌸",
    "هیچی نیست {}! 😊"
]

# وەڵامی خواتان لەگەڵ (کوردی)
BYE_KU = [
    "خواتان لەگەڵ {}! بەڕێز! 🌙",
    "زۆر خۆش بوو لەگەڵت {}! تا دیداری تر! 👋",
    "سەلامەتی {}! 🌸"
]

# وەڵامی خواتان لەگەڵ (فارسی)
BYE_FA = [
    "خدا حافظ {}! بە درود! 🌙",
    "خیلی خوش بود با تو {}! تا دیدار بعد! 👋",
    "سلامتی {}! 🌸"
]

# وەڵامی شەو بخێر (کوردی)
NIGHT_KU = [
    "شەوەکەت پڕ لە ئارامی {}! 🌙💫",
    "خەوی خۆش {}! شەوی خۆش! 🌙",
    "شەو بخێر {}! خەوی خۆش ببینیت! 😴"
]

# وەڵامی شەو بخێر (فارسی)
NIGHT_FA = [
    "شبت پر از آرامش {}! 🌙💫",
    "خواب خوش {}! شب بخیر! 🌙",
    "شب بخیر {}! خواب خوش ببینی! 😴"
]

# ====== فەرمانی /start ======
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply(
        "🎵 **ڕۆڤان بۆت**\n\n"
        "من بۆتێکی گۆرانی و قسەکەرم! 🗣️\n\n"
        "📌 **چی دەتوانم بکەم؟**\n"
        "✅ سڵاو بکەم و بەخێرهاتنت بکەم\n"
        "✅ وەڵامی پرسیارەکانت بدەمەوە\n"
        "✅ گۆرانی پەخش بکەم لە ڤۆیس چات\n\n"
        "🔊 گۆرانیەک بنێرە بۆ پەخشکردن!"
    )

# ====== فەرمانی /ping ======
@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    await message.reply("🏓 پۆنگ! بۆت کاردەکات! ✅\n🏓 پونگ! ربات کار می‌کند! ✅")

# ====== 1. وەڵامدانەوەی ریپلەی ======
@bot.on_message(filters.reply & filters.group)
async def reply_handler(client, message: Message):
    # ئەگەر بۆتەکە ریپلەی کرابوو
    if message.reply_to_message.from_user.id == (await client.get_me()).id:
        user_name = message.from_user.first_name
        text = message.text.lower() if message.text else ""
        
        # دەستنیشانکردنی زمان (کوردی یان فارسی)
        is_farsi = any(word in text for word in ["سلام", "چطوری", "خوب", "ممنون", "خدا", "شب"])
        
        # وەڵامدانەوەی پرسیارە جیاوازەکان
        response = None
        
        # چۆنی؟
        if any(word in text for word in ["چۆنی", "چونی", "چطوری", "چطور"]):
            response = random.choice(HOW_FA if is_farsi else HOW_KU).format(user_name)
        
        # سوپاس
        elif any(word in text for word in ["سوپاس", "سپاس", "ممنون", "مرسی"]):
            response = random.choice(THANK_FA if is_farsi else THANK_KU).format(user_name)
        
        # خواتان لەگەڵ / خداحافظ
        elif any(word in text for word in ["خواتان لەگەڵ", "خدا", "خداحافظ", "بای", "خواحافظ"]):
            response = random.choice(BYE_FA if is_farsi else BYE_KU).format(user_name)
        
        # شەو بخێر
        elif any(word in text for word in ["شەو بخێر", "شب بخیر", "شەو"]):
            response = random.choice(NIGHT_FA if is_farsi else NIGHT_KU).format(user_name)
        
        # سڵاو (ئەگەر هیچ کام نەبێت)
        else:
            response = random.choice(GREETINGS_FA if is_farsi else GREETINGS_KU).format(user_name)
        
        # ناردنی وەڵام بە هەردوو زمان
        await message.reply(f"{response}\n\n💬 {user_name} جان!")

# ====== 2. وەڵامدانەوەی سڵاو (بەبێ ریپلەی) ======
@bot.on_message(filters.text & filters.group & ~filters.reply)
async def greeting_handler(client, message: Message):
    text = message.text.lower()
    user_name = message.from_user.first_name
    
    # دەستنیشانکردنی زمان
    is_farsi = any(word in text for word in ["سلام", "درود"])
    is_kurdish = any(word in text for word in ["سڵاو", "سلاو", "سەلام"])
    
    # سڵاو (کوردی)
    if is_kurdish:
        response = random.choice(GREETINGS_KU).format(user_name)
        await message.reply(f"{response}\n\n🌸 {user_name} جان!")
        return
    
    # سڵاو (فارسی)
    elif is_farsi:
        response = random.choice(GREETINGS_FA).format(user_name)
        await message.reply(f"{response}\n\n🌸 {user_name} جان!")
        return
    
    # چۆنی (کوردی)
    elif any(word in text for word in ["چۆنی", "چونی"]) and not is_farsi:
        response = random.choice(HOW_KU).format(user_name)
        await message.reply(f"{response}\n\n💬 {user_name} جان!")
        return
    
    # چۆنی (فارسی)
    elif any(word in text for word in ["چطوری", "چطور"]):
        response = random.choice(HOW_FA).format(user_name)
        await message.reply(f"{response}\n\n💬 {user_name} جان!")

# ====== 3. وەرگرتنی گۆرانی و ناردنی دوگمەکان ======
@bot.on_message(filters.audio | filters.video | filters.document)
async def audio_handler(client, message: Message):
    chat_id = message.chat.id
    msg_id = message.id
    
    await message.reply(
        "🎵 **گۆرانیەک وەرگیرا!**\n"
        "🎵 **موزیک دریافت شد!**\n\n"
        "▶️ کلیک لەسەر **پلەی** بکە بۆ پەخشکردن\n"
        "▶️ برای پخش کلیک کن\n\n"
        "⏹ کلیک لەسەر **وەستان** بۆ ڕاگرتن\n"
        "⏹ برای توقف کلیک کن",
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
    
    if data.startswith("play_"):
        try:
            parts = data.split("_")
            msg_id = int(parts[2])
            
            await callback_query.answer("⏳ گۆرانی بار دەکرێت...")
            
            msg = await client.get_messages(chat_id, msg_id)
            
            audio_path = None
            song_name = "گۆرانی"
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
            
            await app.join_group_call(
                chat_id,
                AudioPiped(audio_path, audio_parameters=AudioQuality(bitrate=128))
            )
            
            await callback_query.message.reply(
                f"✅ **گۆرانی دەپەخشێت!** 🎵\n"
                f"✅ **موزیک پخش می‌شود!** 🎵\n\n"
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
print("🤖 ڕۆڤان بۆت - Rovan Bot")

async def main():
    try:
        await bot.start()
        print("✅ بۆت دەستپێکرد")
        await user.start()
        print("✅ User Account دەستپێکرد")
        await app.start()
        print("✅ ڤۆیس چات ئامادەیە!")
        print("🎵 بۆت ئامادەیە!")
        await bot.idle()
    except Exception as e:
        print(f"❌ هەڵە: {e}")

import asyncio
asyncio.run(main())
