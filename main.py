import os
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import google.generativeai as genai
import yt_dlp
from youtube_search import YoutubeSearch
import json

# ------------------ ڕێکخستنەکان ------------------
TOKEN = "TOKENI_TELEGRAM_BOT_ET"
API_KEY = "AQ.Ab8RN6KUmypRphJk-2fXKvNbSBOdjODAFTuKW0EFuYDKzZXpkA"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-pro")

# لیستی زمانە پشتیوانی کراوەکان
SUPPORTED_LANGS = ["ckb", "ku", "ar", "en", "fa", "tr"]

# ------------------ فانکشنی یارمەتیدەر ------------------
def get_language(text):
    """زمانی نامە دیاری بکە"""
    # ئەمە سادەیە، دەتوانیت بە libraries وەک langdetect باشتر بکەیت
    if re.search(r'[\u0600-\u06FF]', text):
        return "ar"  # ئەگەر عەرەبی هەیە
    elif re.search(r'[\u{10D00}-\u{10D3F}]', text):  # یونیکۆدی کوردی
        return "ckb"
    elif re.search(r'[a-zA-Z]', text):
        return "en"
    else:
        return "ckb"

def translate_prompt(text, lang):
    """فەرمانی وەرگێڕان بۆ AI"""
    prompts = {
        "ckb": f"وەڵامی ئەم پرسیارە بە کوردی بدەرەوە: {text}",
        "ar": f"أجب على هذا السؤال باللغة العربية: {text}",
        "en": f"Answer this question in English: {text}",
        "fa": f"به این سوال به فارسی پاسخ بده: {text}",
        "tr": f"Bu soruyu Türkçe cevapla: {text}"
    }
    return prompts.get(lang, prompts["ckb"])

# ------------------ فانکشنی سەرەکی بۆت ------------------
async def start(update: Update, context: CallbackContext):
    """1. بەخێرهاتنی خەڵک"""
    user = update.effective_user
    welcome_text = (
        f"🎉 **بەخێربێیت {user.first_name}!**\n\n"
        "من بۆتی AI ی یارمەتیدەرم 💬\n"
        "دەتوانیت لەگەڵم گفتوگۆ بکەیت، گۆرانی بپاڵێژیت، وەڵامی پرسیارەکانت بدەمەوە.\n\n"
        "📌 زمانە پشتیوانی کراون: کوردی، عەرەبی، ئینگلیزی، فارسی، تورکی"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: CallbackContext):
    """3. گفتوگۆی AI لەگەڵ خەڵک بە زمانە جیاوازەکان"""
    text = update.message.text
    if not text:
        return
    
    # دیاریکردنی زمان
    lang = get_language(text)
    
    # دروستکردنی پڕۆمپت
    prompt = translate_prompt(text, lang)
    
    try:
        # وەڵامدانەوەی AI
        response = model.generate_content(prompt)
        reply = response.text if response.text else "نەمتوانی وەڵام بدەمەوە"
        
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"⚠️ هەڵەیەک ڕوویدا: {str(e)}")

async def handle_audio(update: Update, context: CallbackContext):
    """4. گۆرانی لێدان لە ڤۆیس کاڵ"""
    audio = update.message.audio or update.message.voice
    if not audio:
        return
    
    # ناردنی پەیامی چاوەڕوانی
    msg = await update.message.reply_text("🎵 گۆرانیەکە دەپاڵێژم... تکایە چاوەڕوان بە")
    
    try:
        # دەستنیشانکردنی ناوی گۆرانی (ئەگەر هەیە)
        song_name = audio.file_name or "گۆرانی"
        
        # بەکارهێنانی yt-dlp بۆ دەرهێنانی ئۆدیۆ
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # گەڕان بۆ گۆرانی لە یوتیوب
            results = YoutubeSearch(song_name, max_results=1).to_dict()
            if results:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                info = ydl.extract_info(url, download=True)
                audio_file = f"{info['title']}.mp3"
                
                # ناردنی ڤۆیس کاڵ
                with open(audio_file, 'rb') as f:
                    await update.message.reply_audio(
                        audio=f,
                        title=info['title'],
                        performer=info.get('uploader', 'نەزانراو')
                    )
                # سڕینەوەی فایلی کاتی
                os.remove(audio_file)
            else:
                await update.message.reply_text("❌ نەمدۆزییەوە")
        
        # سڕینەوەی پەیامی چاوەڕوانی
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"⚠️ هەڵە: {str(e)}")

async def delete_messages(update: Update, context: CallbackContext):
    """5. سڕینەوەی نامەکان (تەنها بۆ ئەدمین)"""
    # پێویستە ببینرێت ئەم بەکارهەرە ئەدمینە
    if update.effective_user.id not in context.bot_data.get('admins', []):
        await update.message.reply_text("⛔ تەنها ئەدمین دەتوانێت نامە بسڕێتەوە")
        return
    
    # سڕینەوەی نامەی ئێستا
    await update.message.delete()
    await update.message.reply_text("✅ نامە سڕدرایەوە")

async def delete_links(update: Update, context: CallbackContext):
    """6. سڕینەوەی لینکەکان"""
    text = update.message.text
    if not text:
        return
    
    # پشکنینی هەبوونی لینک
    url_pattern = r'https?://[^\s]+'
    if re.search(url_pattern, text):
        try:
            await update.message.delete()
            # ئاگادارکردنەوەی بەکارهەر
            await update.message.reply_text(
                f"🔗 لینک سڕدرایەوە! @{update.effective_user.username or 'بەکارهەر'}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

async def handle_new_member(update: Update, context: CallbackContext):
    """7. سڕینەوەی پاشماوەی هاتنی خەڵک"""
    for member in update.message.new_chat_members:
        # پشکنین بۆ بۆت نەبێت
        if member.is_bot:
            continue
        
        try:
            # سڕینەوەی پەیامی هاتن
            await update.message.delete()
            # پەیامی بەخێرهاتن
            await update.message.reply_text(
                f"🎉 **بەخێربێیت {member.first_name}!**\n"
                "خۆشحاڵین بە هاتنت! 💚"
            )
        except Exception:
            pass

# ------------------ فانکشنی سەرەکی ------------------
def main():
    """دەستپێکردنی بۆت"""
    # دروستکردنی ئەپلیکەیشن
    application = Application.builder().token(TOKEN).build()
    
    # تۆمارکردنی ئەدمینەکان (بۆ سڕینەوەی نامە)
    application.bot_data['admins'] = [123456789]  # ئایدی تۆی و ئەدمینەکان
    
    # هاندلەرەکان
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, handle_audio))
    application.add_handler(MessageHandler(filters.Regex(r'https?://'), delete_links))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    
    # دەستپێکردن
    print("🤖 بۆتەکە کاردەکات...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
