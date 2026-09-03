import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
# گۆڕینی مۆدێل بۆ gemini-pro بۆ ئەوەی کێشەی 404 نەمێنێت
model = genai.GenerativeModel("gemini-pro")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if not user_message:
        return
    try:
        response = model.generate_content(user_message)
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"هەڵە: {e}")
        await update.message.reply_text(f"هەڵەی ڕاستەقینە ئەمەیە: {e}")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("هەڵە: تووکنەکان دابین نەکراون!")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("بۆتەکە دەستی بە کارکردن کرد...")
    app.run_polling()
