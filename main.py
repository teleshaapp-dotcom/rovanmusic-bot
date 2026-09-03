from pyrogram import Client, filters
from pyrogram.types import Message
import os
import random

# ====== گۆڕاوەکان ======
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ====== پێکهێنانی بۆت ======
bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# ====== وەڵامەکان ======
GREETINGS_KU = [
    "سڵاو {}! بەخێربێیت بۆ گروپ! 🌸",
    "سڵاو {}! خۆشحاڵین بە بینینی تۆ! 💫",
    "سڵاو {}! بەخێربێیت! 🌺"
]

GREETINGS_FA = [
    "سلام {}! خوش آمدید به گروه! 🌸",
    "سلام {}! خوشحالیم که اینجایی! 💫",
    "سلام {}! خوش آمدید! 🌺"
]

HOW_KU = ["من باشم {}! تۆ چۆنی؟ 😊", "زۆر باشم {}! تۆ چۆنی؟ 🌸"]
HOW_FA = ["من خوبم {}! تو چطوری؟ 😊", "خیلی خوبم {}! تو چطوری؟ 🌸"]
THANK_KU = ["بەخێربێیت {}! ☺️", "شایەنی سوپاس نەبوو {}! 🌸"]
THANK_FA = ["خواهش می‌کنم {}! ☺️", "قابل شما رو نداره {}! 🌸"]

# ====== فەرمانەکان ======
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply("🎵 **ڕۆڤان بۆت**\n\nمن بۆتێکی قسەکەرم! 🗣️")

@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    await message.reply("🏓 پۆنگ! بۆت کاردەکات! ✅")

# ====== وەڵامدانەوەی ریپلەی ======
@bot.on_message(filters.reply & filters.group)
async def reply_handler(client, message: Message):
    if message.reply_to_message.from_user.id == (await client.get_me()).id:
        user_name = message.from_user.first_name
        text = message.text.lower() if message.text else ""
        
        is_farsi = any(word in text for word in ["سلام", "چطوری", "ممنون"])
        
        if any(word in text for word in ["چۆنی", "چطوری"]):
            response = random.choice(HOW_FA if is_farsi else HOW_KU).format(user_name)
        elif any(word in text for word in ["سوپاس", "ممنون"]):
            response = random.choice(THANK_FA if is_farsi else THANK_KU).format(user_name)
        else:
            response = random.choice(GREETINGS_FA if is_farsi else GREETINGS_KU).format(user_name)
        
        await message.reply(response)

# ====== وەڵامدانەوەی سڵاو ======
@bot.on_message(filters.text & filters.group & ~filters.reply)
async def greeting_handler(client, message: Message):
    text = message.text.lower()
    user_name = message.from_user.first_name
    
    if any(word in text for word in ["سڵاو", "سلاو", "سەلام"]):
        response = random.choice(GREETINGS_KU).format(user_name)
        await message.reply(response)
    elif any(word in text for word in ["سلام", "درود"]):
        response = random.choice(GREETINGS_FA).format(user_name)
        await message.reply(response)

# ====== دەستپێکردن ======
print("🚀 بۆت دەستپێدەکات...")
bot.run()
