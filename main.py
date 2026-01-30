import telebot
import os
from flask import Flask        # Saytcha ochish uchun
import threading               # Bot va Saytni birga yurgizish uchun

# 1. BU YERDA SAYTCHA QISMI BOSHLANADI
app = Flask('')

@app.route('/')
def home():
    return "Bot yoniq!"        # Saytga kirganda shu yozuv chiqadi

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Saytni alohida "yo'lak"da yurgizib qo'yamiz
threading.Thread(target=run).start()

# 2. BU YERDA BOTINGIZNING ASOSIY QISMI BOSHLANADI
TOKEN = '7994354084:AAEJutacknUKBBBD8E7xv5N9G-qWrYrN7_A'  # Shu yerga bot tokeningizni qo'ying
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def salom(message):
    bot.reply_to(message, "Salom! Bot 24/7 rejimida ishlamoqda.")

# Qolgan barcha kodlaringizni (testlar, pdf-lar) shu yerga qo'shib ketaverasiz

# 3. BOTNI ISHGA TUSHIRISH
if __name__ == "__main__":
    bot.infinity_polling()
