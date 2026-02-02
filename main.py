import telebot
import sqlite3
import google.generativeai as genai
from telebot import types

# --- SOZLAMALAR ---
API_TOKEN = '7994354084:AAEJutacknUKBBBD8E7xv5N9G-qWrYrN7_A'
ADMIN_ID = 8317043750  # O'zingizning ID raqamingiz (raqamlarda)
GEMINI_KEY = 'AIzaSyD-sbFPC77OTDKkz0ObI0AplQzr0YEkdTI'

bot = telebot.TeleBot(API_TOKEN)

# Gemini AI sozlamasi
try:
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"AI ulanishda xato: {e}")


# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect('test_center.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS active_test 
                 (id INTEGER PRIMARY KEY, answers TEXT, file_id TEXT, is_active INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results 
                 (user_id INTEGER, name TEXT, score TEXT, percent REAL)''')
    conn.commit()
    conn.close()


init_db()


# --- ADMIN TUGMALARI ---
def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Yangi Test Yuklash 📄", "Testni To'xtatish 🛑")
    return markup


# --- START ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Xush kelibsiz, Ustoz! Test boshlash uchun quyidagi tugmani bosing:",
                         reply_markup=admin_keyboard())
    else:
        bot.send_message(message.chat.id, "Assalomu alaykum! Testda qatnashish uchun /jointest buyrug'ini bosing.")


# --- TEST YUKLASH ---
@bot.message_handler(func=lambda m: m.text == "Yangi Test Yuklash 📄")
def start_new_test(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.send_message(message.chat.id, "Testning PDF faylini yuboring:")
    bot.register_next_step_handler(msg, get_pdf)


def get_pdf(message):
    if message.content_type == 'document':
        file_id = message.document.file_id
        msg = bot.send_message(message.chat.id, "Endi to'g'ri javoblarni yuboring (masalan: abcd...):")
        bot.register_next_step_handler(msg, lambda m: save_test(m, file_id))
    else:
        bot.send_message(message.chat.id, "Iltimos, faqat fayl (PDF) yuboring!")


def save_test(message, file_id):
    answers = message.text.lower().strip()
    conn = sqlite3.connect('test_center.db')
    c = conn.cursor()
    c.execute("DELETE FROM active_test")
    c.execute("INSERT INTO active_test (answers, file_id, is_active) VALUES (?, ?, 1)", (answers, file_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Test faol! Kalitlar: {answers}\nO'quvchilar javob yuborishi mumkin.")


# --- TESTNI TO'XTATISH ---
@bot.message_handler(func=lambda m: m.text == "Testni To'xtatish 🛑")
def stop_test(message):
    if message.from_user.id != ADMIN_ID: return
    conn = sqlite3.connect('test_center.db')
    c = conn.cursor()
    c.execute("UPDATE active_test SET is_active = 0")
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "🛑 Test to'xtatildi. Endi javoblar qabul qilinmaydi.")


# --- O'QUVCHI UCHUN ---
@bot.message_handler(commands=['jointest'])
def join_test(message):
    conn = sqlite3.connect('test_center.db')
    c = conn.cursor()
    c.execute("SELECT file_id, is_active FROM active_test LIMIT 1")
    test = c.fetchone()
    conn.close()

    if test and test[1] == 1:
        bot.send_document(message.chat.id, test[0], caption="Test fayli. Ismingizni kiriting:")
        bot.register_next_step_handler(message, get_student_name)
    else:
        bot.send_message(message.chat.id, "Hozirda hech qanday faol test yo'q.")


def get_student_name(message):
    name = message.text
    msg = bot.send_message(message.chat.id,
                           f"Rahmat {name}. Endi faqat javoblarni bitta qilib yuboring (masalan: abcd...):")
    bot.register_next_step_handler(msg, lambda m: check_answers(m, name))


def check_answers(message, name):
    conn = sqlite3.connect('test_center.db')
    c = conn.cursor()
    c.execute("SELECT answers, is_active FROM active_test LIMIT 1")
    test = c.fetchone()

    if test and test[1] == 1:
        correct_answers = test[0]
        student_ans = message.text.lower().strip()

        if len(student_ans) != len(correct_answers):
            msg = bot.send_message(message.chat.id,
                                   f"⚠️ Xato! Javoblar soni {len(correct_answers)} ta bo'lishi kerak. Qaytadan kiriting:")
            bot.register_next_step_handler(msg, lambda m: check_answers(m, name))
            return

        corrects = sum(1 for a, b in zip(student_ans, correct_answers) if a == b)
        percent = (corrects / len(correct_answers)) * 100

        # Ustozga hisobot
        report = (
            f"📝 Yangi natija:\n👤 O'quvchi: {name}\n✅ To'g'ri: {corrects}/{len(correct_answers)}\n📊 Foiz: {percent}%")
        bot.send_message(ADMIN_ID, report)
        bot.send_message(message.chat.id, "✅ Javoblaringiz qabul qilindi. Natija ustozga yuborildi.")
    else:
        bot.send_message(message.chat.id, "❌ Uzr, test vaqti tugagan.")
    conn.close()


# --- AI BILAN SUHBAT ---
@bot.message_handler(func=lambda m: True)
def chat_with_ai(message):
    try:
        response = ai_model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except:
        bot.reply_to(message, "Hozircha AI javob bera olmaydi, lekin test tizimi ishlayapti.")


# BOTNI ISHGA TUSHIRISH
print("Bot ishga tushdi...")
bot.infinity_polling()
