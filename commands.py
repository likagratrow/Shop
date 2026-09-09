"""Команды бота из меню Telegram."""

import json
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


def _is_care_or_repair_order(message):
    try:
        data = json.loads(message.web_app_data.data)
        return any(
            isinstance(product, dict)
            and str(product.get("category", "")).strip().lower() in {"care", "repair"}
            for product in data.get("products", [])
        )
    except Exception:
        return False


@_bot().message_handler(func=lambda message: _is_care_or_repair_order(message), content_types=["web_app_data"])
def care_or_repair_web_app_data(message):
    data = json.loads(message.web_app_data.data)
    for product in data.get("products", []):
        if isinstance(product, dict) and str(product.get("category", "")).strip().lower() in {"care", "repair"}:
            product["category"] = "repeat"
    message.web_app_data.data = json.dumps(data, ensure_ascii=False)
    _main().web_app_data(message)


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
