import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# بەکارهێنانی ناوی ڕاستەوخۆی مۆدێلەکە بۆ کتێبخانەکە
model = genai.GenerativeModel('gemini-pro')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    # ١. بەخێرهاتنی کەسی نوێ بۆ گروپ و سڕینەوەی نامەی پاشماوە
    if message.new_chat_members:
        for member in message.new_chat_members:
            welcome_text = f"بەخێر بێیت بۆ گروپ، {member.full_name} گیان! 😊"
            await message.reply_text(welcome_text)
        
        try:
            await message.delete()
        except Exception as e:
            print(f"ناتوانێت نامەی جۆین بسڕێتەوە: {e}")
        return

    # ٢. وەڵامدانەوەی AI لە گروپدا تەنها کاتێک ڕیپلەی بۆتەکە بکرێت
    if message.chat.type in ["group", "supergroup"]:
        if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
            user_message = message.text
            if not user_message:
                return
            try:
                await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
                response = model.generate_content(user_message)
                await message.reply_text(response.text)
            except Exception as e:
                await message.reply_text(f"هەڵە ڕووی دا: {e}")
    else:
        # چاتی تایبەت (Private)
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
    app.add_handler(MessageHandler(filters.TEXT | filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_message))
    
    print("بۆتەکە دەستی بە کارکردن کرد...")
    app.run_polling()
