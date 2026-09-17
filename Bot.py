import json
import urllib.request
from telebot import types
import telebot
from config import BOT_TOKEN
import individual_order
import reviews

YOUR_TELEGRAM_ID = 5219493908
WEB_APP_URL = "https://likagratrow.github.io/Shop/"
STOCK_API_URL = "https://script.google.com/macros/s/AKfycbwwQkE9C1U82T0LoYv9umYrc-pmeD0KSZPZ0IOWAtEvWrKGagUNPJeoUvtIyviQF4-vfoTg/exec"
CONTACT_TEXT = "Спасибо! Для завершения оформления заказа отправьте номер телефона или, если удобнее, свяжемся через Telegram"
REPEAT_CONTACT_TEXT = "Пожалуйста оставьте контакт (telegram или если удобнее, телефон), и мы свяжемся с вами по поводу изготовления заказа. Спасибо!"
MIXED_CONTACT_TEXT = "Пожалуйста оставьте контакт (telegram или если удобнее, телефон), и мы свяжемся с вами по поводу изготовления заказа. Остальные товары будут доставлены как обычно. Спасибо!"

bot = telebot.TeleBot(BOT_TOKEN)
orders_db = {}
import commands


def shop_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("🛍 Магазин", web_app=types.WebAppInfo(url=WEB_APP_URL)),
        types.InlineKeyboardButton("📅 Записаться", web_app=types.WebAppInfo(url="https://likagratrow.github.io/Booking/"))
    )
    keyboard.row(types.InlineKeyboardButton("🧵 Индивидуальный заказ", callback_data="menu_individual"))
    keyboard.row(types.InlineKeyboardButton("💬 Обратная связь", callback_data="menu_feedback"))
    return keyboard


individual_order._shop_keyboard = shop_keyboard
reviews._shop_keyboard = shop_keyboard


def contact_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    keyboard.row(types.KeyboardButton("💬 Не отправлять номер, связаться в ТГ"))
    return keyboard


def format_price(value):
    try:
        return f"{int(value):,}".replace(",", " ") + " ₽"
    except Exception:
        return f"{value} ₽"


def remove_inline_buttons(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception as error:
        print("Не удалось скрыть кнопки:", error)


def request_contact(chat_id, text=None, reason=None):
    order = orders_db.setdefault(chat_id, {})
    order["waiting_contact"] = True
    order["contact_required"] = True
    if reason:
        order["contact_reason"] = reason
    bot.send_message(chat_id, text or CONTACT_TEXT, reply_markup=contact_keyboard())


def send_final_order_message(chat_id):
    order = orders_db.get(chat_id)
    if not order:
        return

    if order.get("repeat_order"):
        text = "Спасибо!\n\nМастер свяжется с вами в рабочее время Пн–Пт 10-18."
    elif order.get("delivery_id") == "courier_ekb":
        text = "Спасибо!\n\nВсё-всё записал и передал менеджеру) Сборка заказа обычно занимает один рабочий день, затем мы с вами свяжемся и обрадуем, что готовы организовать доставку. Спасибо за заказ!"
    else:
        text = "Спасибо!\n\nВсё-всё записал и передал менеджеру) Сборка заказа обычно занимает один рабочий день, затем мы с вами свяжемся и обрадуем, что можно забрать (или что он отправлен). Спасибо за заказ!"

    bot.send_message(chat_id, text, reply_markup=shop_keyboard())


def send_owner_notification(chat_id):
    order = orders_db.get(chat_id)
    if not order or order.get("completed"):
        return

    if not order.get("paid_status") and not order.get("waiting_manager") and not order.get("contact_required"):
        return

    order["completed"] = True

    items = order.get("items", "")
    delivery_title = order.get("delivery_title")
    delivery_price = order.get("delivery_price")
    delivery_service = order.get("delivery_service")
    delivery_country = order.get("delivery_country")
    delivery_address = order.get("delivery_address")
    payable_total = order.get("payable_total", order.get("total", 0))
    repeat_product_total = order.get("repeat_product_total", 0)
    total = order.get("total", payable_total)

    owner_text = "🛍 НОВЫЙ ЗАКАЗ\n\n"

    if order.get("repeat_order") or order.get("mixed_order"):
        owner_text += "⚒️ НА ЗАКАЗ\n\n"

    owner_text += f"{items}\n\n💰 К оплате сейчас: {format_price(payable_total)}\n"

    if repeat_product_total:
        owner_text += f"⚒️ На заказ: {format_price(repeat_product_total)}\n"

    if delivery_title:
        if delivery_price is None:
            owner_text += f"🚚 Доставка: {delivery_title} (стоимость по согласованию)\n"
        else:
            owner_text += f"🚚 Доставка: {delivery_title} — {format_price(delivery_price)}\n"

    if delivery_service:
        owner_text += f"📦 Служба доставки: {delivery_service}\n"
    if delivery_country:
        owner_text += f"🌍 Страна: {delivery_country}\n"
    if delivery_address:
        owner_text += f"📍 Куда доставить: {delivery_address}\n"

    owner_text += f"\n💰 Итого: <b>{format_price(total)}</b>\n"
    owner_text += f"\n👤 Клиент: {order.get('first_name') or ''}\n"

    if order.get("username"):
        owner_text += f"💬 Telegram: @{order['username']}\n"

    owner_text += f"📱 Телефон: {order['phone']}\n" if order.get("phone") else "📱 Телефон: не предоставлен\n"

    if order.get("contact_reason"):
        owner_text += f"\n⚠️ Причина обращения: {order['contact_reason']}"
    elif order.get("waiting_manager"):
        owner_text += "\n⏳ Клиент ожидает диалога перед оплатой."
    elif order.get("paid_status"):
        owner_text += "\n💳 Клиент подтвердил оплату."

    bot.send_message(YOUR_TELEGRAM_ID, owner_text, parse_mode="HTML")


def finish_repeat_order(chat_id):
    order = orders_db.get(chat_id)
    if not order or order.get("completed"):
        return
    send_owner_notification(chat_id)
    send_final_order_message(chat_id)


def decrement_stock(order):
    products = order.get("products", [])
    if not isinstance(products, list) or not products:
        return False, "В заказе отсутствует список товаров."

    normalized = []

    for product in products:
        if not isinstance(product, dict):
            return False, "Некорректные данные товара."

        category = str(product.get("category", "")).strip().lower()
        if category == "repeat":
            continue

        product_id = str(product.get("id", "")).strip()
        if not product_id:
            return False, "Некорректные данные товара."

        try:
            quantity = int(product.get("quantity"))
        except (TypeError, ValueError):
            return False, "Некорректное количество товара."

        if quantity < 1:
            return False, "Некорректное количество товара."

        normalized.append({"id": product_id, "quantity": quantity})

    if not normalized:
        return True, None

    payload = json.dumps(
        {"action": "check_and_decrement", "items": normalized},
        ensure_ascii=False
    ).encode("utf-8")

    request = urllib.request.Request(
        STOCK_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))

        print("Ответ системы остатков:", result)
        return (True, None) if result.get("ok") else (False, result.get("error", "Не удалось обновить остатки."))

    except urllib.error.HTTPError as error:
        print("HTTP-ошибка списания остатков:", error.code)
        return False, "Не удалось связаться с системой остатков."
    except urllib.error.URLError as error:
        print("Ошибка соединения с системой остатков:", error.reason)
        return False, "Не удалось связаться с системой остатков."
    except Exception as error:
        print("Ошибка списания остатков:", repr(error))
        return False, "Не удалось связаться с системой остатков."


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в Странные Вещи.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.send_message(
        message.chat.id,
        "Выберите, что хотите сделать.",
        reply_markup=shop_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == "menu_individual")
def individual_order_callback(call):
    bot.answer_callback_query(call.id)
    individual_order.start(bot, call.message.chat.id, orders_db)


@bot.callback_query_handler(func=lambda call: call.data == "menu_feedback")
def feedback_callback(call):
    bot.answer_callback_query(call.id)
    reviews.start(bot, call.message.chat.id, orders_db)


@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid(call):
    chat_id = call.message.chat.id
    remove_inline_buttons(call)
    order = orders_db.get(chat_id)

    if not order:
        bot.answer_callback_query(call.id, "Заказ не найден.")
        return

    if order.get("paid_status"):
        bot.answer_callback_query(call.id, "Оплата уже отмечена.")
        return

    ok, error = decrement_stock(order)

    if not ok:
        reason = "Не удалось подтвердить наличие товара"
        order["contact_reason"] = reason

        try:
            bot.answer_callback_query(call.id, error or reason)
        except Exception:
            pass

        if error == "Not enough stock":
            message_text = "⚠️ Не удалось подтвердить наличие товара.\n\n" + CONTACT_TEXT
        else:
            message_text = str(error) + "\n\n" + CONTACT_TEXT

        request_contact(chat_id, message_text, reason=reason)
        return

    order["paid_status"] = True

    try:
        bot.answer_callback_query(call.id, "Оплата отмечена.")
    except Exception:
        pass

    request_contact(
        chat_id,
        MIXED_CONTACT_TEXT if order.get("mixed_order") else CONTACT_TEXT
    )


@bot.callback_query_handler(func=lambda call: call.data == "wait_manager")
def wait_manager(call):
    chat_id = call.message.chat.id
    remove_inline_buttons(call)
    order = orders_db.get(chat_id)

    if not order:
        bot.answer_callback_query(call.id, "Заказ не найден.")
        return

    order["waiting_manager"] = True
    bot.answer_callback_query(call.id, "Хорошо")
    request_contact(
        chat_id,
        MIXED_CONTACT_TEXT if order.get("mixed_order") else CONTACT_TEXT
    )


@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    chat_id = message.chat.id
    order = orders_db.get(chat_id)

    if not order or not order.get("waiting_contact"):
        return

    order["phone"] = message.contact.phone_number
    order["waiting_contact"] = False

    if order.get("contact_reason"):
        send_owner_notification(chat_id)
        bot.send_message(
            chat_id,
            "Спасибо! Я передал информацию менеджеру, мы свяжемся с вами для уточнения деталей.",
            reply_markup=shop_keyboard()
        )
        return

    if order.get("repeat_order"):
        finish_repeat_order(chat_id)
        return

    if order.get("mixed_order"):
        send_owner_notification(chat_id)
        if order.get("paid_status"):
            send_final_order_message(chat_id)
        elif order.get("waiting_manager"):
            bot.send_message(
                chat_id,
                "Хорошо 😊\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.",
                reply_markup=shop_keyboard()
            )
        return

    if order.get("paid_status"):
        send_owner_notification(chat_id)
        send_final_order_message(chat_id)
    elif order.get("waiting_manager"):
        send_owner_notification(chat_id)
        bot.send_message(
            chat_id,
            "Хорошо 😊\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.",
            reply_markup=shop_keyboard()
        )


@bot.message_handler(func=lambda message: message.text == "💬 Не отправлять номер, связаться в ТГ")
def no_phone(message):
    chat_id = message.chat.id
    order = orders_db.get(chat_id)

    if not order or not order.get("waiting_contact"):
        return

    order["phone"] = None
    order["waiting_contact"] = False

    if order.get("contact_reason"):
        send_owner_notification(chat_id)
        bot.send_message(
            chat_id,
            "Спасибо! Я передал информацию менеджеру, мы свяжемся с вами для уточнения деталей.",
            reply_markup=shop_keyboard()
        )
        return

    if order.get("repeat_order"):
        finish_repeat_order(chat_id)
        return

    if order.get("mixed_order"):
        send_owner_notification(chat_id)
        if order.get("paid_status"):
            send_final_order_message(chat_id)
        elif order.get("waiting_manager"):
            bot.send_message(
                chat_id,
                "Хорошо 😊\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.",
                reply_markup=shop_keyboard()
            )
        return

    if order.get("paid_status"):
        send_owner_notification(chat_id)
        send_final_order_message(chat_id)
    elif order.get("waiting_manager"):
        send_owner_notification(chat_id)
        bot.send_message(
            chat_id,
            "Хорошо 😊\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.",
            reply_markup=shop_keyboard()
        )


@bot.message_handler(func=lambda message: True)
def text_handler(message):
    chat_id = message.chat.id
    order = orders_db.get(chat_id)

    if order and order.get("waiting_individual_description"):
        order["individual_description"] = message.text
        order["waiting_individual_description"] = False
        request_contact(chat_id)
        return

    if order and order.get("waiting_feedback"):
        order["feedback_text"] = message.text
        order["waiting_feedback"] = False

        if message.from_user.username:
            bot.send_message(
                YOUR_TELEGRAM_ID,
                f"💬 НОВАЯ ОБРАТНАЯ СВЯЗЬ\n\n{message.text}\n\n👤 Клиент: {message.from_user.first_name or ''}\n💬 Telegram: @{message.from_user.username}"
            )
        else:
            bot.send_message(
                YOUR_TELEGRAM_ID,
                f"💬 НОВАЯ ОБРАТНАЯ СВЯЗЬ\n\n{message.text}\n\n👤 Клиент: {message.from_user.first_name or ''}"
            )

        bot.send_message(
            chat_id,
            "Спасибо! Ваше сообщение передано.",
            reply_markup=shop_keyboard()
        )
        return


print("Бот запущен")
bot.infinity_polling()
