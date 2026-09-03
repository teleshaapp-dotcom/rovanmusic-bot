import asyncio
import os

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# -----------------------------------------------------------------
# هەموو نهێنییەکان (API_ID, API_HASH, BOT_TOKEN, STRING_SESSION) دەبێت
# لە Railway -> Variables دابنرێن، هەرگیز لێرە بە شێوەی ڕاستەوخۆ ننووسرێن.
# -----------------------------------------------------------------
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
STRING_SESSION = os.environ["STRING_SESSION"]  # لە session_generator.py وەریدەگریت

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# بۆتی ئاسایی (Bot API) - وەرگرتنی کۆماند و فایلی گۆرانی
bot = Client(
    "rovanmusic_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# هەژماری ڕاستەقینە (Userbot) - چوونە ناو Voice Chat
user = Client(
    "rovanmusic_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
)

call_py = PyTgCalls(user)


@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "سڵاو غازی گیان! بۆتی مۆزیک لەسەر ڕێپۆزیتۆری نوێ بە سەرکەوتوویی ئامادە شد و کار دەکات 🎵\n\n"
        "گۆرانییەک وەک فایلی دەنگ بنێرە بۆ گروپەکە، بۆتەکە خۆکارانە دەیخاتە ناو ڤۆیس چات.\n"
        "کۆماندی /stop بۆ ڕاگرتنی مۆزیک."
    )


@bot.on_message(filters.audio | filters.voice)
async def handle_audio(client, message):
    chat_id = message.chat.id

    status_msg = await message.reply_text("⏳ گۆرانییەکە دادەبەزێنم...")

    try:
        file_path = await message.download(file_name=f"{DOWNLOAD_DIR}/")
    except Exception as e:
        await status_msg.edit_text(f"❌ نەمتوانی گۆرانییەکە دابگرم: {e}")
        return

    try:
        # ئەگەر پێشتر لە voice chat جوینکراوە، play دەیگۆڕێت
        try:
            await call_py.play(chat_id, MediaStream(file_path))
        except Exception:
            await call_py.join_group_call(chat_id, MediaStream(file_path))

        await status_msg.edit_text("🎶 گۆرانییەکە ئێستا لە ڤۆیس چاتی گروپەکە دەدرێت.")
    except Exception as e:
        await status_msg.edit_text(
            f"❌ نەمتوانرا بچمە ناو ڤۆیس چات. دڵنیابەرەوە کە ڤۆیس چات کراوەیە لە گروپەکە.\nهەڵە: {e}"
        )
    finally:
        # فایلە خوارەوەکە دەسڕینەوە بۆ پاراستنی بۆشایی دیسک
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@bot.on_message(filters.command("stop"))
async def stop_command(client, message):
    chat_id = message.chat.id
    try:
        await call_py.leave_call(chat_id)
        await message.reply_text("⏹️ مۆزیکەکە ڕاگیرا و لە ڤۆیس چات دەرچووم.")
    except Exception as e:
        await message.reply_text(f"هەڵە لە ڕاگرتن: {e}")


async def main():
    await user.start()
    await bot.start()
    await call_py.start()
    print("Bot is starting...")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
