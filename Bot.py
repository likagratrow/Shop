import json
import threading
import time
import urllib.error
import urllib.request
from telebot import types
import telebot
from config import BOT_TOKEN
import individual_order
import reviews

YOUR_TELEGRAM_ID = 5219493908
WEB_APP_URL = 'https://likagratrow.github.io/Shop/'
ORDERS_API_URL = 'https://script.google.com/macros/s/AKfycbz2XQn7s0e_irZ2rRsvcXb_I7hKp_DxNXTYsZlIt2TATE58IiqJ9AyjUKj9f09-CII9/exec'
NEWS_URL = 'https://t.me/strannstuff'

bot = telebot.TeleBot(BOT_TOKEN)
orders_db = {}


def shop_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton('🛍 Магазин', web_app=types.WebAppInfo(url=WEB_APP_URL)),
        types.InlineKeyboardButton('📅 Записаться', web_app=types.WebAppInfo(url='https://likagratrow.github.io/Booking/'))
    )
    keyboard.row(types.InlineKeyboardButton('🧵 Особый заказ', callback_data='menu_individual'))
    keyboard.row(
        types.InlineKeyboardButton('💬 Обратная связь', callback_data='menu_feedback'),
        types.InlineKeyboardButton('📰 Новости', url=NEWS_URL)
    )
    return keyboard


individual_order._shop_keyboard = shop_keyboard
reviews._shop_keyboard = shop_keyboard


def _attach_phone_to_latest_order(telegram_id, phone, attempts=4):
    payload = json.dumps({
        'action': 'attach-order-phone',
        'api_token': BOT_TOKEN,
        'telegram_id': str(telegram_id),
        'phone': str(phone)
    }, ensure_ascii=False).encode('utf-8')

    request = urllib.request.Request(
        ORDERS_API_URL,
        data=payload,
        headers={
            'Content-Type': 'text/plain;charset=utf-8',
            'User-Agent': 'Mozilla/5.0'
        },
        method='POST'
    )

    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
            print('Привязка телефона к заказу:', result)
            return
        except Exception as error:
            print('Не удалось привязать телефон к заказу:', repr(error))
            if attempt + 1 < attempts:
                time.sleep(1)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        'Добро пожаловать в Странные Вещи.',
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.send_message(
        message.chat.id,
        'Выберите, что хотите сделать.',
        reply_markup=shop_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'menu_individual')
def individual_order_callback(call):
    bot.answer_callback_query(call.id)
    individual_order.start(bot, call.message.chat.id, orders_db)


@bot.callback_query_handler(func=lambda call: call.data == 'menu_feedback')
def feedback_callback(call):
    bot.answer_callback_query(call.id)
    reviews.start(bot, call.message.chat.id, orders_db)


@bot.message_handler(content_types=['contact'])
def store_contact(message):
    chat_id = message.chat.id
    order = orders_db.get(chat_id) or {}

    # Эти ветки сами обрабатывают контакт.
    if order.get('individual_order') or order.get('feedback'):
        return

    phone = str(message.contact.phone_number or '').strip()
    if not phone:
        return

    threading.Thread(
        target=_attach_phone_to_latest_order,
        args=(message.from_user.id, phone),
        daemon=True
    ).start()


import commands


print('Бот запущен')
bot.infinity_polling()
