import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
# بەکارهێنانی مۆدێلی گونجاو
model = genai.GenerativeModel("gemini-1.5-flash")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    # ١. بەخێرهاتنی کەسی نوێ بۆ گروپ و سڕینەوەی نامەی پاشماوەی جۆین
    if message.new_chat_members:
        for member in message.new_chat_members:
            # ناردنی نامەی بەخێرهاتن
            welcome_text = f"بەخێر بێیت بۆ گروپ، {member.full_name} گیان! 😊"
            await message.reply_text(welcome_text)
        
        # سڕینەوەی پاشماوەی چوونەژوورەوەی ئەندامەکە (بۆ ئەوەی گروپەکە پیس نەبێت)
        try:
            await message.delete()
        except Exception as e:
            print(f"ناتوانێت نامەی جۆین بسڕێتەوە (پێویستە بۆتەکە ئەمنیشی هەبێت): {e}")
        return

    # ٢. وەڵامدانەوەی AI تەنها کاتێک کەسێک ڕیپلەی بۆتەکە بکات لە گروپدا (یاخود لە چاتی تایبەت)
    if message.chat.type in ["group", "supergroup"]:
        # پشکنین ئایا نامەکە ڕیپلەی بۆتەکەیە یان نا
        if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
            user_message = message.text
            if not user_message:
                return
            try:
                # ناردنی نیشانەی نووسین (Typing)
                await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
                
                response = model.generate_content(user_message)
                await message.reply_text(response.text)
            except Exception as e:
                await message.reply_text(f"هەڵە ڕووی دا: {e}")
    else:
        # ئەگەر لە چاتی تایبەت (Private) بوو، ئاسایی وەڵام بداتەوە
        user_message = message.text
        if user_message:
            try:
                response = model.generate_content(user_message)
                await message.reply_text(response.text)
            except Exception as e:
                await message.reply_text(f"هەڵە: {e}")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("هەڵە: تووکنەکان دابین نەکراون!")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # وەرگرتنی هەموو دەقەکان و چالاکییەکان
    app.add_handler(MessageHandler(filters.TEXT | filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_message))
    
    print("بۆتەکە دەستی بە کارکردن کرد...")
    app.run_polling()
