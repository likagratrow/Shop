"""Команды бота из меню Telegram."""

import sys
import os
import threading
import time
import telebot
from telebot import types
import individual_order
import reviews


POLLING_WATCHDOG_TIMEOUT = 120
_polling_last_activity = time.monotonic()


def _polling_get_updates_with_watchdog(original_get_updates):
    def wrapped(self, *args, **kwargs):
        global _polling_last_activity
        _polling_last_activity = time.monotonic()
        try:
            return original_get_updates(self, *args, **kwargs)
        finally:
            _polling_last_activity = time.monotonic()

    return wrapped


def _polling_watchdog():
    while True:
        time.sleep(15)
        silence = time.monotonic() - _polling_last_activity
        if silence >= POLLING_WATCHDOG_TIMEOUT:
            print(
                f"Polling не отвечает {int(silence)} сек. "
                "Перезапускаю бота..."
            )
            os.execv(sys.executable, [sys.executable] + sys.argv)


_original_get_updates = telebot.TeleBot.get_updates
telebot.TeleBot.get_updates = _polling_get_updates_with_watchdog(_original_get_updates)
threading.Thread(target=_polling_watchdog, daemon=True).start()


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
    _bot().send_message(
        message.chat.id,
        "Кнопка магазина в меню ниже поля ввода. Нажмите на значок кнопок там, где обычно пишете сообщение (около скрепки). Спасибо!"
    )


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


# Orders — отдельный Apps Script-сервис магазина.
# Регистрируем его до основных callback-хендлеров Bot.py.
import orders_bridge
orders_bridge.register()
