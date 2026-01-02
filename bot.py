from telebot import TeleBot, types
import os
import json
import uuid
import time

# ================= تنظیمات =================
TOKEN = "8136214686:AAGCdLlmG_TpQfY7N_A5zkdwepsAOqy4fuI"
ADMIN_ID = 7358112045   # آیدی عددی خودت
DATA_FILE = "data.json"
FILES_DIR = "files"

bot = TeleBot(TOKEN)

# ================= آماده‌سازی =================
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
else:
    db = {}

def save_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

user_state = {}

# ================= شروع ربات =================
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📤 ارسال فایل", "📥 دریافت فایل")
    bot.send_message(message.chat.id, "یکی از گزینه‌ها را انتخاب کن یا از /help استفاده کن:", reply_markup=markup)
    user_state[message.chat.id] = None


# ================= دریافت پیام‌ها =================
@bot.message_handler(content_types=["text", "document", "photo", "video"])
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    # انتخاب گزینه‌ها
    if text == "📤 ارسال فایل":
        user_state[chat_id] = "waiting_file"
        bot.send_message(chat_id, "فایل مورد نظر را ارسال کن")
        return

    if text == "📥 دریافت فایل":
        user_state[chat_id] = "waiting_code"
        bot.send_message(chat_id, "کدی که دریافت کرده‌ای را ارسال کن")
        return
    
    if text == "📤 ارسال فایل":
        user_state[chat_id] = "waiting_file"
        bot.send_message(chat_id, "فایل مورد نظر را ارسال کن")
        return

    if text == "/help":
        user_state[chat_id] = "waiting_code"
        bot.send_message(chat_id, "🔵برای استفاده از ربات روی یکی از گزینه ها بزنید" \
        "🔴وقتی روی گزینه ی ارسال فایل می زنید فایل مورد نظر با حجم زیر 50 مگابایت را ارسال کنید ربات فابل را ذخیره می کند و یک کد اختصاصی به شما می دهد که برای باز گردانی فایل نیاز است" \
        "🟡برای بازگردانی فایل روی دریافت فایل بزنید و کد اختصاصی فایل مورد نظر را ارسال کنید تا ربات پس از چند لحظه فایل را برای شما ارسال کند ." \
        "برای شروع روی /start بزنید")
        return

    # ================= دریافت فایل =================
    if user_state.get(chat_id) == "waiting_file":

        file_id = None
        filename = None

        if message.document:
            file_id = message.document.file_id
            filename = message.document.file_name

        elif message.video:
            file_id = message.video.file_id
            filename = f"{file_id}.mp4"

        elif message.photo:
            file_id = message.photo[-1].file_id
            filename = f"{file_id}.jpg"

        else:
            bot.send_message(chat_id, "❌ فرمت فایل پشتیبانی نمی‌شود")
            return

        try:
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)
        except Exception as e:
            bot.send_message(chat_id, "❌ خطا در دریافت فایل")
            print(e)
            return

        code = str(uuid.uuid4())[:8]
        file_path = os.path.join(FILES_DIR, f"{code}_{filename}")

        with open(file_path, "wb") as f:
            f.write(downloaded)

        db[code] = file_path
        save_db()

        bot.send_message(chat_id, f"✅ فایل ذخیره شد\nکد شما: `{code}`", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"📥 فایل جدید\nکد: {code}\nاز کاربر: {chat_id}")

        user_state[chat_id] = None
        return

    # ================= ارسال فایل با کد =================
    if user_state.get(chat_id) == "waiting_code":
        code = text.strip()

        if code not in db:
            bot.send_message(chat_id, "❌ کد نامعتبر است")
            return

        path = db[code]

        try:
            with open(path, "rb") as f:
                if path.lower().endswith((".mp4", ".mov", ".mkv")):
                    bot.send_video(chat_id, f, timeout=120)
                else:
                    bot.send_document(chat_id, f, timeout=120)

            bot.send_message(chat_id, "✅ فایل ارسال شد")

        except Exception as e:
            bot.send_message(chat_id, "❌ خطا در ارسال فایل")
            print("SEND ERROR:", e)

        user_state[chat_id] = None
        return

    # پیام نامعتبر
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📤 ارسال فایل", "📥 دریافت فایل")
    bot.send_message(chat_id, "از منو استفاده کن 👇 و برای توضیح کار با ان /help", reply_markup=markup)


# ================= اجرا =================
bot.polling(non_stop=True, interval=0, timeout=120)
