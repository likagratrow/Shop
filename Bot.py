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
    state = orders_db.get(message.chat.id) or {}

    # Индивидуальный заказ и обратная связь обрабатывают свои контакты сами.
    if state.get('individual_order') or state.get('feedback'):
        return

    phone = str(message.contact.phone_number or '').strip()
    if not phone:
        return

    payload = json.dumps({
        'action': 'receive-contact',
        'api_token': BOT_TOKEN,
        'telegram_id': str(message.from_user.id),
        'phone': phone
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

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
        print('Передача Telegram contact в Orders:', result)
    except Exception as error:
        print('Не удалось передать Telegram contact в Orders:', repr(error))



import commands


print('Бот запущен')
bot.infinity_polling()
