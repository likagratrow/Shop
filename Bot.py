import json
import urllib.parse
import urllib.request
from telebot import types
import telebot

from config import BOT_TOKEN


YOUR_TELEGRAM_ID = 5219493908
WEB_APP_URL = "https://likagratrow.github.io/Shop/"
SHEET_ID = "1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk"
STOCK_API_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbwwkQeC1U82T0LoYv9umYrc-pmeD0KSZP0IOWAtEvWrKGagUNPJeoUvtIyviQF4-vfoTg"
    "/exec"
)
DELIVERY_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
    f"?sheet=%D0%94%D0%BE%D1%81%D1%82%D0%B0%D0%B2%D0%BA%D0%B0"
)

bot = telebot.TeleBot(BOT_TOKEN)
orders_db = {}


def shop_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        types.KeyboardButton("🛍 Магазин", web_app=types.WebAppInfo(url=WEB_APP_URL)),
        types.KeyboardButton("📅 Записаться")
    )
    keyboard.row(types.KeyboardButton("🧵 Индивидуальный заказ"))
    keyboard.row(types.KeyboardButton("💬 Обратная связь"))
    return keyboard


def contact_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    keyboard.row(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    keyboard.row(types.KeyboardButton("💬 Не отправлять номер, связаться в ТГ"))
    return keyboard


def load_delivery_options():
    options = []
    try:
        with urllib.request.urlopen(DELIVERY_SHEET_URL, timeout=10) as response:
            text = response.read().decode("utf-8")

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Не удалось найти JSON в ответе Google Sheets")

        data = json.loads(text[start:end + 1])
        rows = data.get("table", {}).get("rows", [])

        for row in rows:
            cells = row.get("c", [])
            values = []
            for cell in cells:
                if cell is None:
                    values.append("")
                else:
                    values.append(str(cell.get("v", "")).strip())

            if len(values) < 3:
                continue

            delivery_id = values[0]
            title = values[1]
            price_raw = values[2]
            if not delivery_id or not title:
                continue

            price = None
            if price_raw:
                try:
                    price = float(
                        price_raw.replace(" ", "").replace(",", ".").replace("₽", "")
                    )
                    if price.is_integer():
                        price = int(price)
                except Exception:
                    price = None

            options.append({"id": delivery_id, "title": title, "price": price})

        return options

    except Exception as error:
        print("Ошибка загрузки доставки:", error)
        return []


def delivery_keyboard(options):
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    for option in options:
        if option["price"] is None:
            price_text = "договорная"
        else:
            price_text = f"{option['price']:,} ₽".replace(",", " ")

        keyboard.row(
            types.KeyboardButton(f"{option['title']} ({price_text})")
        )
    return keyboard


def delivery_service_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    keyboard.row(types.KeyboardButton("Яндекс"))
    keyboard.row(types.KeyboardButton("Ozon"))
    keyboard.row(types.KeyboardButton("5Post"))
    return keyboard


def format_price(value):
    try:
        return f"{int(value):,}".replace(",", " ") + " ₽"
    except Exception:
        return f"{value} ₽"


def request_contact(chat_id, text=None, reason=None):
    order = orders_db.setdefault(chat_id, {})
    order["waiting_contact"] = True
    order["contact_required"] = True
    if reason:
        order["contact_reason"] = reason

    if text is None:
        text = (
            "Оставьте пожалуйста контакт, в рабочее время мы с вами "
            "свяжемся и оформим заказ!"
        )

    bot.send_message(
        chat_id,
        text,
        reply_markup=contact_keyboard()
    )


def send_owner_notification(chat_id):
    order = orders_db.get(chat_id)
    if not order or order.get("completed"):
        return

    if not order.get("paid_status") and not order.get("waiting_manager") and not order.get("contact_required"):
        return

    order["completed"] = True

    username = order.get("username")
    first_name = order.get("first_name") or ""
    phone = order.get("phone")
    items = order.get("items", "")
    product_total = order.get("product_total", order.get("total", 0))
    delivery_title = order.get("delivery_title")
    delivery_price = order.get("delivery_price")
    delivery_service = order.get("delivery_service")
    delivery_address = order.get("delivery_address")
    total = order.get("total", product_total)

    owner_text = (
        "🛍 НОВЫЙ ЗАКАЗ\n\n"
        f"{items}\n\n"
        f"💰 Товары: {format_price(product_total)}\n"
    )

    if delivery_title:
        if delivery_price is None:
            owner_text += (
                f"🚚 Доставка: {delivery_title} "
                "(стоимость по согласованию)\n"
            )
        else:
            owner_text += (
                f"🚚 Доставка: {delivery_title} — "
                f"{format_price(delivery_price)}\n"
            )

    if delivery_service:
        owner_text += f"📦 Служба доставки: {delivery_service}\n"

    if delivery_address:
        owner_text += f"📍 Куда доставить: {delivery_address}\n"

    owner_text += "\n"

    if delivery_price is None and delivery_title:
        owner_text += (
            f"💰 Итого: <b>{format_price(product_total)}</b> + "
            "доставка по согласованию\n"
        )
    else:
        owner_text += f"💰 Итого: <b>{format_price(total)}</b>\n"

    owner_text += "\n"
    owner_text += f"👤 Клиент: {first_name}\n"

    if username:
        owner_text += f"💬 Telegram: @{username}\n"

    if phone:
        owner_text += f"📱 Телефон: {phone}\n"
    else:
        owner_text += "📱 Телефон: не предоставлен\n"

    if order.get("contact_reason"):
        owner_text += f"\n⚠️ Причина обращения: {order['contact_reason']}"
    elif order.get("waiting_manager"):
        owner_text += "\n⏳ Клиент ожидает диалога перед оплатой."
    else:
        owner_text += "\n💳 Клиент подтвердил оплату."

    bot.send_message(YOUR_TELEGRAM_ID, owner_text, parse_mode="HTML")


def decrement_stock(order):
    products = order.get("products", [])
    if not isinstance(products, list) or not products:
        return False, "В заказе отсутствует список товаров."

    normalized_products = []
    for product in products:
        if not isinstance(product, dict):
            return False, "Некорректные данные товара."

        product_id = str(product.get("id", "")).strip()
        quantity = product.get("quantity")
        if not product_id:
            return False, "Некорректные данные товара."

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return False, "Некорректное количество товара."

        if quantity < 1:
            return False, "Некорректное количество товара."

        normalized_products.append({"id": product_id, "quantity": quantity})

    payload = json.dumps(
        {"action": "check_and_decrement", "items": normalized_products},
        ensure_ascii=False
    ).encode("utf-8")

    request = urllib.request.Request(
        STOCK_API_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            text = response.read().decode("utf-8")

        result = json.loads(text)
        print("Ответ системы остатков:", result)

        if result.get("ok"):
            return True, None

        return False, result.get("error", "Не удалось обновить остатки.")

    except urllib.error.HTTPError as error:
        try:
            error_text = error.read().decode("utf-8", errors="replace")
        except Exception:
            error_text = ""
        print("HTTP-ошибка списания остатков:", error.code, error_text)
        return False, "Не удалось связаться с системой остатков."

    except urllib.error.URLError as error:
        print("Ошибка соединения с системой остатков:", error.reason)
        return False, "Не удалось связаться с системой остатков."

    except Exception as error:
        print("Ошибка списания остатков:", repr(error))
        return False, "Не удалось связаться с системой остатков."


def get_delivery_address_prompt(delivery_id):
    if delivery_id == "courier_ekb":
        return (
            "📍 Напишите вручную адрес, куда привезти заказ.\n\n"
            "Нужен адрес квартиры: улица, дом, квартира 😊"
        )

    if delivery_id == "russia":
        return None

    if delivery_id == "abroad":
        return (
            "🌍 Напишите вручную страну, в которую отправляем заказ.\n\n"
            "Детали доставки мы согласуем с вами отдельно 😊"
        )

    return None


def send_payment_message(chat_id):
    order = orders_db.get(chat_id)
    if not order:
        return

    items = order.get("items", "")
    product_total = order.get("product_total", order.get("total", 0))
    delivery_title = order.get("delivery_title")
    delivery_price = order.get("delivery_price")
    delivery_service = order.get("delivery_service")
    delivery_address = order.get("delivery_address")
    total = order.get("total", product_total)

    customer_text = "Ваш заказ:\n\n" + f"{items}\n\n" + f"💰 Товары: {format_price(product_total)}\n"

    if delivery_title:
        if delivery_price is None:
            customer_text += f"🚚 Доставка: {delivery_title} (стоимость по согласованию)\n"
        else:
            customer_text += f"🚚 Доставка: {delivery_title} — {format_price(delivery_price)}\n"

    if delivery_service:
        customer_text += f"📦 Служба доставки: {delivery_service}\n"

    if delivery_address:
        customer_text += f"📍 Куда доставить: {delivery_address}\n"

    customer_text += "\n"

    if delivery_price is None and delivery_title:
        customer_text += (
            f"💰 Итого: <b>{format_price(product_total)}</b> + "
            "доставка по согласованию\n\n"
            "📦 Стоимость доставки будет согласована с менеджером.\n\n"
        )
    else:
        customer_text += f"💰 Итого: <b>{format_price(total)}</b>\n\n"

    customer_text += (
        "💳 Оплата переводом на Сбербанк:\n"
        "📱 +79089147913\n"
        "👤 Получатель: Лия П.\n\n"
        "📦 Заказ будет собран после оплаты.\n\n"
        "Вы можете перевести оплату сейчас или дождаться связи с менеджером "
        "в рабочее время:\n"
        "Пн–Пт, 10:00–18:00 (Екатеринбург)."
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton("💳 Я оплатил", callback_data="paid"))
    keyboard.row(types.InlineKeyboardButton("⏳ Подожду менеджера", callback_data="wait_manager"))

    bot.send_message(
        chat_id,
        customer_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@bot.message_handler(commands=["start"])
def start(message):
    orders_db[message.chat.id] = {}
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в Странные Вещи.\n"
        "Выберите, что хотите сделать.",
        reply_markup=shop_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "📅 Записаться")
def handle_booking(message):
    bot.send_message(
        message.chat.id,
        "Вы можете записаться на мастер-класс или Диоген по адресу: https://dikidi.ru/2143045?p=0.pi-si&o=13&s=23280541"
    )


@bot.message_handler(func=lambda message: message.text == "🧵 Индивидуальный заказ")
def handle_custom_order(message):
    bot.send_message(message.chat.id, "Опишите, что бы вы хотели заказать?")


@bot.message_handler(func=lambda message: message.text == "💬 Обратная связь")
def handle_feedback(message):
    bot.send_message(message.chat.id, "Чем бы вы хотели поделиться?")


@bot.message_handler(content_types=["web_app_data"])
def handle_web_app_data(message):
    chat_id = message.chat.id

    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception as delete_error:
        print("Не удалось удалить техническое сообщение:", delete_error)

    try:
        data = json.loads(message.web_app_data.data)
    except Exception as error:
        print("Ошибка разбора данных Mini App:", error)
        request_contact(
            chat_id,
            "Не удалось прочитать заказ. Оставьте пожалуйста контакт, в рабочее время мы с вами свяжемся и оформим заказ!",
            "Не удалось прочитать заказ"
        )
        return

    products = data.get("products", [])
    if not isinstance(products, list):
        products = []

    items = str(data.get("items", "")).strip().replace(", ", "\n")
    total = data.get("total", 0)
    needs_delivery = bool(data.get("needs_delivery", False))

    orders_db[chat_id] = {
        "items": items,
        "products": products,
        "product_total": total,
        "total": total,
        "needs_delivery": needs_delivery,
        "delivery_id": None,
        "delivery_title": None,
        "delivery_price": None,
        "delivery_service": None,
        "delivery_address": None,
        "paid_status": None,
        "phone": None,
        "username": message.from_user.username if message.from_user else None,
        "user_id": message.from_user.id if message.from_user else chat_id,
        "first_name": message.from_user.first_name if message.from_user else "",
        "waiting_manager": False,
        "waiting_contact": False,
        "waiting_delivery": False,
        "waiting_delivery_service": False,
        "waiting_delivery_address": False,
        "contact_required": False,
        "completed": False
    }

    if not needs_delivery:
        send_payment_message(chat_id)
        return

    options = load_delivery_options()
    if not options:
        request_contact(
            chat_id,
            "Не удалось загрузить варианты доставки. Оставьте пожалуйста контакт, в рабочее время мы с вами свяжемся и оформим заказ!",
            "Не удалось загрузить варианты доставки"
        )
        return

    order = orders_db[chat_id]
    order["waiting_delivery"] = True

    bot.send_message(
        chat_id,
        "🚚 Выберите способ доставки:",
        reply_markup=delivery_keyboard(options)
    )


@bot.message_handler(
    func=lambda message: orders_db.get(message.chat.id, {}).get("waiting_delivery", False)
)
def handle_delivery(message):
    chat_id = message.chat.id
    order = orders_db.get(chat_id)
    if not order:
        return

    options = load_delivery_options()
    selected_option = None

    for option in options:
        price_text = "договорная" if option["price"] is None else f"{option['price']:,} ₽".replace(",", " ")
        expected_text = f"{option['title']} ({price_text})"
        if message.text == expected_text:
            selected_option = option
            break

    if not selected_option:
        bot.send_message(
            chat_id,
            "Пожалуйста, выберите вариант доставки одной из кнопок ниже.",
            reply_markup=delivery_keyboard(options)
        )
        return

    order["waiting_delivery"] = False
    order["delivery_id"] = selected_option["id"]
    order["delivery_title"] = selected_option["title"]
    order["delivery_price"] = selected_option["price"]

    product_total = order.get("product_total", order.get("total", 0))
    order["total"] = product_total if selected_option["price"] is None else product_total + selected_option["price"]

    if selected_option["id"] == "russia":
        order["waiting_delivery_service"] = True
        bot.send_message(
            chat_id,
            "📦 Выберите службу доставки:",
            reply_markup=delivery_service_keyboard()
        )
        return

    prompt = get_delivery_address_prompt(selected_option["id"])
    if prompt:
        order["waiting_delivery_address"] = True
        bot.send_message(
            chat_id,
            prompt,
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    send_payment_message(chat_id)


@bot.message_handler(
    func=lambda message: orders_db.get(message.chat.id, {}).get("waiting_delivery_service", False)
)
def handle_delivery_service(message):
    if message.text not in ("Яндекс", "Ozon", "5Post"):
        return

    order = orders_db.get(message.chat.id)
    if not order:
        return

    order["delivery_service"] = message.text
    order["waiting_delivery_service"] = False
    order["waiting_delivery_address"] = True

    bot.send_message(
        message.chat.id,
        "📍 Напишите вручную адрес, куда отправить заказ.\n\n"
        "Можно просто указать город и адрес выбранного ПВЗ 😊",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(
    func=lambda message: orders_db.get(message.chat.id, {}).get("waiting_delivery_address", False)
)
def handle_delivery_address(message):
    chat_id = message.chat.id
    order = orders_db.get(chat_id)
    if not order:
        return

    address = (message.text or "").strip()
    if not address:
        bot.send_message(chat_id, "Напишите, пожалуйста, адрес ещё раз 😊")
        return

    order["delivery_address"] = address
    order["waiting_delivery_address"] = False
    send_payment_message(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid(call):
    chat_id = call.message.chat.id
    order = orders_db.get(chat_id)

    if not order:
        bot.answer_callback_query(call.id, "Заказ не найден.")
        return

    if order.get("paid_status") == "paid":
        bot.answer_callback_query(call.id, "Оплата уже отмечена.")
        return

    stock_ok, stock_error = decrement_stock(order)

    if not stock_ok:
        bot.answer_callback_query(
            call.id,
            "Не удалось подтвердить наличие товара.",
            show_alert=True
        )
        request_contact(
            chat_id,
            "⚠️ Не удалось подтвердить наличие товара.\n\n"
            "Оставьте пожалуйста контакт, в рабочее время мы с вами свяжемся и оформим заказ!",
            "Не удалось подтвердить наличие товара"
        )
        return

    order["paid_status"] = "paid"

    bot.answer_callback_query(call.id, "Спасибо!")

    try:
        bot.edit_message_reply_markup(
            chat_id,
            call.message.message_id,
            reply_markup=None
        )
    except Exception as edit_error:
        print("Не удалось убрать кнопки оплаты:", edit_error)

    bot.send_message(
        chat_id,
        "Спасибо! 💳\n\n"
        "Оплата отмечена. Заказ принят в работу."
    )

    send_owner_notification(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "wait_manager")
def wait_manager(call):
    chat_id = call.message.chat.id
    order = orders_db.get(chat_id)

    if not order:
        bot.answer_callback_query(call.id, "Заказ не найден.")
        return

    order["waiting_manager"] = True
    bot.answer_callback_query(call.id)

    try:
        bot.edit_message_reply_markup(
            chat_id,
            call.message.message_id,
            reply_markup=None
        )
    except Exception as edit_error:
        print("Не удалось убрать кнопки оплаты:", edit_error)

    bot.send_message(
        chat_id,
        "Хорошо 😊\n\n"
        "Менеджер свяжется с вами в рабочее время Пн-Пт 10-18.",
        reply_markup=shop_keyboard()
    )

    send_owner_notification(chat_id)


@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    chat_id = message.chat.id
    order = orders_db.setdefault(chat_id, {})
    order["phone"] = message.contact.phone_number
    order["waiting_contact"] = False

    if order.get("paid_status") or order.get("waiting_manager") or order.get("contact_required"):
        send_owner_notification(chat_id)


@bot.message_handler(
    func=lambda message: message.text == "💬 Не отправлять номер, связаться в ТГ"
)
def no_phone(message):
    chat_id = message.chat.id
    order = orders_db.setdefault(chat_id, {})
    order["waiting_contact"] = False
    order["phone"] = None

    if order.get("paid_status") or order.get("waiting_manager") or order.get("contact_required"):
        send_owner_notification(chat_id)


@bot.message_handler(func=lambda message: message.text == "🛍 Магазин")
def open_shop(message):
    return


if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling(skip_pending=True)
