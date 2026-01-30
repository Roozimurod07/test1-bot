import telebot
import sqlite3
import os
from flask import Flask
import threading

# --- SOZLAMALAR ---
API_TOKEN = '7994354084:AAEJutacknUKBBBD8E7xv5N9G-qWrYrN7_A' 
ADMIN_ID = 8317043750 # O'zingizning Telegram ID-ingiz

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('test.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS active_test (answers TEXT, file_id TEXT, is_active INTEGER)')
    conn.commit()
    conn.close()

init_db()

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Yangi Test Yuklash 📄", "Testni To'xtatish 🛑")
        bot.send_message(message.chat.id, "Xush kelibsiz, Ustoz!", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Assalomu alaykum! Testda qatnashish uchun /jointest deb yozing.")

@bot.message_handler(func=lambda m: m.text == "Yangi Test Yuklash 📄")
def upload_test(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "PDF faylni yuboring:")
        bot.register_next_step_handler(msg, save_pdf)

def save_pdf(message):
    if message.content_type == 'document':
        fid = message.document.file_id
        msg = bot.send_message(message.chat.id, "Kalitlarni yuboring (masalan: abcd...):")
        bot.register_next_step_handler(msg, lambda m: finish_setup(m, fid))

def finish_setup(message, fid):
    ans = message.text.lower().strip()
    conn = get_db()
    conn.execute("DELETE FROM active_test")
    conn.execute("INSERT INTO active_test VALUES (?, ?, 1)", (ans, fid))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Test faol!")

@bot.message_handler(func=lambda m: m.text == "Testni To'xtatish 🛑")
def stop(message):
    if message.from_user.id == ADMIN_ID:
        conn = get_db()
        conn.execute("UPDATE active_test SET is_active = 0")
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "🛑 Test to'xtatildi.")

@bot.message_handler(commands=['jointest'])
def join(message):
    conn = get_db()
    t = conn.execute("SELECT file_id, is_active FROM active_test").fetchone()
    conn.close()
    if t and t[1] == 1:
        bot.send_document(message.chat.id, t[0], caption="Ismingizni kiriting:")
        bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(message.chat.id, "Hozir test yo'q.")

def get_name(message):
    name = message.text
    msg = bot.send_message(message.chat.id, f"Rahmat {name}. Javoblarni yuboring:")
    bot.register_next_step_handler(msg, lambda m: check(m, name))

def check(message, name):
    conn = get_db()
    t = conn.execute("SELECT answers, is_active FROM active_test").fetchone()
    if t and t[1] == 1:
        correct = t[0]
        student = message.text.lower().strip()
        if len(student) == len(correct):
            ball = sum(1 for a, b in zip(student, correct) if a == b)
            bot.send_message(ADMIN_ID, f"👤 {name}\n✅ Ball: {score}/{len(correct)}")
            bot.send_message(message.chat.id, "Natija yuborildi!")
        else:
            bot.send_message(message.chat.id, f"Xato! {len(correct)} ta javob bo'lishi kerak.")
    else:
        bot.send_message(message.chat.id, "Vaqt tugagan!")

@app.route('/')
def home(): return "OK"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))).start()
    bot.infinity_polling()
