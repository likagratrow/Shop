"""Команды бота из меню Telegram."""

import sys
from telebot import types
import individual_order
import reviews


def _main():
    return sys.modules["__main__"]


def _bot():
    return _main().bot


def _orders_db():
    return _main().orders_db


def _web_app_url():
    return _main().WEB_APP_URL


@_bot().message_handler(commands=["shop"])
def shop_command(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(types.KeyboardButton("🛍 Магазин", web_app=types.WebAppInfo(url=_web_app_url())))
    _bot().send_message(message.chat.id, "🛍 Открыть магазин:", reply_markup=keyboard)


@_bot().message_handler(commands=["booking"])
def booking_command(message):
    _bot().send_message(
        message.chat.id,
        "Вы можете записаться на мастер-класс или Диоген по адресу: https://dikidi.ru/2143045?p=0.pi-si&o=13&s=23280541"
    )


@_bot().message_handler(commands=["order"])
def order_command(message):
    individual_order.start(_bot(), message.chat.id, _orders_db())


@_bot().message_handler(commands=["feedback"])
def feedback_command(message):
    reviews.start(_bot(), message.chat.id, _orders_db())
