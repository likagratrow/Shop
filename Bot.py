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
ACCESS_INVITE_API_URL = 'https://script.google.com/macros/s/AKfycbzs21P908JOT1KBK3c-iH8m7ofkIvsBwMF9pSDWCaj14Y05z7Q-ukkJ1h3OBkNB-t0p/exec'

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



def _start_parameter(message):
    text = str(getattr(message, 'text', '') or '').strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return ''
    return parts[1].strip()


def _redeem_access_invite(message, token):
    if not token:
        return True, ''

    payload = json.dumps({
        'action': 'redeem-invite',
        'token': str(token),
        'telegram_id': str(message.from_user.id),
        'username': str(message.from_user.username or '')
    }, ensure_ascii=False).encode('utf-8')

    request = urllib.request.Request(
        ACCESS_INVITE_API_URL,
        data=payload,
        headers={
            'Content-Type': 'text/plain;charset=utf-8',
            'User-Agent': 'Mozilla/5.0'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))

        if not result.get('ok'):
            return False, str(result.get('error') or 'Не удалось активировать приглашение.')

        return True, ''

    except Exception as error:
        print('Ошибка активации приглашения:', repr(error))
        return False, 'Не удалось активировать приглашение. Попробуйте ещё раз позже.'


@bot.message_handler(commands=['start'])
def start(message):
    token = _start_parameter(message)

    if token:
        ok, error = _redeem_access_invite(message, token)
        if not ok:
            bot.send_message(
                message.chat.id,
                'Не удалось активировать приглашение.\n\n' + error
            )
            return

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


_MENU_CALLBACKS = {
    'menu_individual': individual_order.start,
    'menu_feedback': reviews.start,
}


@bot.callback_query_handler(func=lambda call: call.data in _MENU_CALLBACKS)
def menu_callback(call):
    bot.answer_callback_query(call.id)
    _MENU_CALLBACKS[call.data](bot, call.message.chat.id, orders_db)


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
