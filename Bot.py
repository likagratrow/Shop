import json
import urllib.request
from telebot import types
import telebot
from config import BOT_TOKEN

YOUR_TELEGRAM_ID = 5219493908
WEB_APP_URL = "https://likagratrow.github.io/Shop/"
SHEET_ID = "1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk"
STOCK_API_URL = "https://script.google.com/macros/s/AKfycbwwQkE1C0x82T0LoYv9umYrc-pmeD0KSZP0IOWAtEvWrKGagUNPJeoUvtIyviQF4-vfoTg/exec"
DELIVERY_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?sheet=%D0%94%D0%BE%D1%81%D1%82%D0%B0%D0%B2%D0%BA%D0%B0"
CONTACT_TEXT = "Спасибо! Для завершения оформления заказа отправьте номер телефона или, если удобнее, свяжемся через Telegram"
REPEAT_CONTACT_TEXT = "Отличный выбор! Чтобы мы могли обсудить детали, оставьте пожалуйста контакты - Telegram или, если удобнее, то номер телефона."

bot = telebot.TeleBot(BOT_TOKEN)
orders_db = {}


def shop_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(types.KeyboardButton("🛍 Магазин", web_app=types.WebAppInfo(url=WEB_APP_URL)), types.KeyboardButton("📅 Записаться"))
    keyboard.row(types.KeyboardButton("🧵 Индивидуальный заказ"))
    keyboard.row(types.KeyboardButton("💬 Обратная связь"))
    return keyboard


def contact_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    keyboard.row(types.KeyboardButton("💬 Не отправлять номер, связаться в ТГ"))
    return keyboard


def load_delivery_options():
    try:
        with urllib.request.urlopen(DELIVERY_SHEET_URL, timeout=10) as response:
            text = response.read().decode("utf-8")
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Не удалось найти JSON в ответе Google Sheets")
        data = json.loads(text[start:end + 1])
        result = []
        for row in data.get("table", {}).get("rows", []):
            values = ["" if c is None else str(c.get("v", "")).strip() for c in row.get("c", [])]
            if len(values) < 3 or not values[0] or not values[1]:
                continue
            price = None
            if values[2]:
                try:
                    price = float(values[2].replace(" ", "").replace(",", ".").replace("₽", ""))
                    if price.is_integer(): price = int(price)
                except Exception: pass
            result.append({"id": values[0], "title": values[1], "price": price})
        return result
    except Exception as error:
        print("Ошибка загрузки доставки:", error)
        return []


def delivery_keyboard(options):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for option in options:
        price = "договорная" if option["price"] is None else f"{option['price']:,} ₽".replace(",", " ")
        keyboard.row(types.KeyboardButton(f"{option['title']} ({price})"))
    return keyboard


def delivery_service_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for name in ("Яндекс", "Ozon", "5Post"):
        keyboard.row(types.KeyboardButton(name))
    return keyboard


def format_price(value):
    try: return f"{int(value):,}".replace(",", " ") + " ₽"
    except Exception: return f"{value} ₽"


def request_contact(chat_id, text=None, reason=None):
    order = orders_db.setdefault(chat_id, {})
    order["waiting_contact"] = True
    order["contact_required"] = True
    if reason: order["contact_reason"] = reason
    bot.send_message(chat_id, text or CONTACT_TEXT, reply_markup=contact_keyboard())


def send_final_order_message(chat_id):
    order = orders_db.get(chat_id)
    if not order: return
    if order.get("repeat_order"):
        text = "Спасибо!\n\nМастер свяжется с вами в рабочее время Пн-Пт 10-18."
    elif order.get("delivery_id") == "courier_ekb":
        text = "Спасибо!\n\nВсё-всё записал и передал менеджеру) Сборка заказа обычно занимает один рабочий день, затем мы с вами свяжемся и обрадуем, что готовы организовать доставку. Спасибо за заказ!"
    else:
        text = "Спасибо!\n\nВсё-всё записал и передал менеджеру) Сборка заказа обычно занимает один рабочий день, затем мы с вами свяжемся и обрадуем, что можно забрать (или что он отправлен). Спасибо за заказ!"
    bot.send_message(chat_id, text, reply_markup=shop_keyboard())


def send_owner_notification(chat_id):
    order = orders_db.get(chat_id)
    if not order or order.get("completed"): return
    if not order.get("paid_status") and not order.get("waiting_manager") and not order.get("contact_required"): return
    order["completed"] = True
    items = order.get("items", "")
    product_total = order.get("product_total", order.get("total", 0))
    delivery_title = order.get("delivery_title")
    delivery_price = order.get("delivery_price")
    delivery_service = order.get("delivery_service")
    delivery_address = order.get("delivery_address")
    total = order.get("total", product_total)
    owner_text = "🛍 НОВЫЙ ЗАКАЗ\n\n"
    if order.get("repeat_order"): owner_text += "⚒️ НА ЗАКАЗ\n\n"
    owner_text += f"{items}\n\n💰 Товары: {format_price(product_total)}\n"
    if delivery_title:
        owner_text += f"🚚 Доставка: {delivery_title} — {format_price(delivery_price)}\n" if delivery_price is not None else f"🚚 Доставка: {delivery_title} (стоимость по согласованию)\n"
    if delivery_service: owner_text += f"📦 Служба доставки: {delivery_service}\n"
    if delivery_address: owner_text += f"📍 Куда доставить: {delivery_address}\n"
    owner_text += "\n"
    owner_text += f"💰 Итого: <b>{format_price(product_total)}</b> + доставка по согласованию\n" if delivery_price is None and delivery_title else f"💰 Итого: <b>{format_price(total)}</b>\n"
    owner_text += f"\n👤 Клиент: {order.get('first_name') or ''}\n"
    if order.get("username"): owner_text += f"💬 Telegram: @{order['username']}\n"
    owner_text += f"📱 Телефон: {order['phone']}\n" if order.get("phone") else "📱 Телефон: не предоставлен\n"
    if order.get("repeat_order"):
        pass
    elif order.get("contact_reason"):
        owner_text += f"\n⚠️ Причина обращения: {order['contact_reason']}"
    elif order.get("waiting_manager"):
        owner_text += "\n⏳ Клиент ожидает диалога перед оплатой."
    else:
        owner_text += "\n💳 Клиент подтвердил оплату."
    bot.send_message(YOUR_TELEGRAM_ID, owner_text, parse_mode="HTML")


def finish_repeat_order(chat_id):
    order = orders_db.get(chat_id)
    if not order or order.get("completed"): return
    send_owner_notification(chat_id)
    send_final_order_message(chat_id)


def decrement_stock(order):
    products = order.get("products", [])
    if not isinstance(products, list) or not products: return False, "В заказе отсутствует список товаров."
    normalized = []
    for product in products:
        if not isinstance(product, dict): return False, "Некорректные данные товара."
        product_id = str(product.get("id", "")).strip()
        if not product_id: return False, "Некорректные данные товара."
        try: quantity = int(product.get("quantity"))
        except (TypeError, ValueError): return False, "Некорректное количество товара."
        if quantity < 1: return False, "Некорректное количество товара."
        normalized.append({"id": product_id, "quantity": quantity})
    payload = json.dumps({"action": "check_and_decrement", "items": normalized}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(STOCK_API_URL, data=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=15) as response: result = json.loads(response.read().decode("utf-8"))
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


def get_delivery_address_prompt(delivery_id):
    if delivery_id == "courier_ekb": return "📍 Напишите вручную адрес, куда привезти заказ.\n\nНужен адрес квартиры: улица, дом, квартира 😊"
    if delivery_id == "russia": return None
    if delivery_id == "abroad": return "🌍 Напишите вручную страну, в которую отправляем заказ.\n\nДетали доставки мы согласуем с вами отдельно 😊"
    return None


def send_payment_message(chat_id):
    order = orders_db.get(chat_id)
    if not order: return
    items = order.get("items", ""); product_total = order.get("product_total", order.get("total", 0)); delivery_title = order.get("delivery_title"); delivery_price = order.get("delivery_price"); delivery_service = order.get("delivery_service"); delivery_address = order.get("delivery_address"); total = order.get("total", product_total)
    text = "Ваш заказ:\n\n" + f"{items}\n\n💰 Товары: {format_price(product_total)}\n"
    if delivery_title: text += f"🚚 Доставка: {delivery_title} (стоимость по согласованию)\n" if delivery_price is None else f"🚚 Доставка: {delivery_title} — {format_price(delivery_price)}\n"
    if delivery_service: text += f"📦 Служба доставки: {delivery_service}\n"
    if delivery_address: text += f"📍 Куда доставить: {delivery_address}\n"
    text += "\n"
    if delivery_price is None and delivery_title: text += f"💰 Итого: <b>{format_price(product_total)}</b> + доставка по согласованию\n\n📦 Стоимость доставки будет согласована с менеджером.\n\n"
    else: text += f"💰 Итого: <b>{format_price(total)}</b>\n\n"
    text += "💳 Оплата переводом на Сбербанк:\n📱 +79089147913\n👤 Получатель: Лия П.\n\n📦 Заказ будет собран после оплаты.\n\nВы можете перевести оплату сейчас или дождаться связи с менеджером в рабочее время:\nПн–Пт, 10:00–18:00 (Екатеринбург)."
    keyboard = types.InlineKeyboardMarkup(); keyboard.row(types.InlineKeyboardButton("💳 Я оплатил", callback_data="paid")); keyboard.row(types.InlineKeyboardButton("⏳ Подожду менеджера", callback_data="wait_manager"))
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


def start_delivery(chat_id, reason=None):
    options = load_delivery_options()
    if not options:
        request_contact(chat_id, "Не удалось загрузить варианты доставки. " + CONTACT_TEXT, "Не удалось загрузить варианты доставки")
        return
    orders_db[chat_id]["waiting_delivery"] = True
    bot.send_message(chat_id, "🚚 Выберите способ доставки:", reply_markup=delivery_keyboard(options))


@bot.message_handler(commands=["start"])
def start(message):
    orders_db[message.chat.id] = {}
    bot.send_message(message.chat.id, "Добро пожаловать в Странные Вещи.\nВыберите, что хотите сделать.", reply_markup=shop_keyboard())

@bot.message_handler(func=lambda message: message.text == "📅 Записаться")
def handle_booking(message):
    bot.send_message(message.chat.id, "Вы можете записаться на мастер-класс или Диоген по адресу: https://dikidi.ru/2143045?p=0.pi-si&o=13&s=23280541")

@bot.message_handler(func=lambda message: message.text == "🧵 Индивидуальный заказ")
def handle_custom_order(message): bot.send_message(message.chat.id, "Опишите, что бы вы хотели заказать?")

@bot.message_handler(func=lambda message: message.text == "💬 Обратная связь")
def handle_feedback(message): bot.send_message(message.chat.id, "Чем бы вы хотели поделиться?")


@bot.message_handler(content_types=["web_app_data"])
def handle_web_app_data(message):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except Exception as error: print("Не удалось удалить техническое сообщение:", error)
    try: data = json.loads(message.web_app_data.data)
    except Exception as error:
        print("Ошибка разбора данных Mini App:", error); request_contact(chat_id, "Не удалось прочитать заказ. " + CONTACT_TEXT, "Не удалось прочитать заказ"); return
    products = data.get("products", []); products = products if isinstance(products, list) else []
    items = str(data.get("items", "")).strip().replace(", ", "\n")
    total = data.get("total", 0); needs_delivery = bool(data.get("needs_delivery", False))
    repeat_order = bool(products) and all(isinstance(p, dict) and str(p.get("category", "")).strip().lower() == "repeat" for p in products)
    orders_db[chat_id] = {"items": items, "products": products, "product_total": total, "total": total, "needs_delivery": needs_delivery, "repeat_order": repeat_order, "delivery_id": None, "delivery_title": None, "delivery_price": None, "delivery_service": None, "delivery_address": None, "paid_status": None, "phone": None, "username": message.from_user.username if message.from_user else None, "user_id": message.from_user.id if message.from_user else chat_id, "first_name": message.from_user.first_name if message.from_user else "", "waiting_manager": False, "waiting_contact": False, "waiting_delivery": False, "waiting_delivery_service": False, "waiting_delivery_address": False, "contact_required": False, "completed": False}
    if repeat_order:
        request_contact(chat_id, REPEAT_CONTACT_TEXT)
        return
    if not needs_delivery: send_payment_message(chat_id); return
    start_delivery(chat_id)


@bot.message_handler(func=lambda message: orders_db.get(message.chat.id, {}).get("waiting_delivery", False))
def handle_delivery(message):
    chat_id = message.chat.id; order = orders_db.get(chat_id)
    if not order: return
    options = load_delivery_options(); selected = None
    for option in options:
        price = "договорная" if option["price"] is None else f"{option['price']:,} ₽".replace(",", " ")
        if message.text == f"{option['title']} ({price})": selected = option; break
    if not selected:
        bot.send_message(chat_id, "Пожалуйста, выберите вариант доставки одной из кнопок ниже.", reply_markup=delivery_keyboard(options)); return
    order["waiting_delivery"] = False; order["delivery_id"] = selected["id"]; order["delivery_title"] = selected["title"]; order["delivery_price"] = selected["price"]
    product_total = order.get("product_total", order.get("total", 0)); order["total"] = product_total if selected["price"] is None else product_total + selected["price"]
    if selected["id"] == "russia":
        order["waiting_delivery_service"] = True; bot.send_message(chat_id, "📦 Выберите службу доставки:", reply_markup=delivery_service_keyboard()); return
    prompt = get_delivery_address_prompt(selected["id"])
    if prompt:
        order["waiting_delivery_address"] = True; bot.send_message(chat_id, prompt, reply_markup=types.ReplyKeyboardRemove()); return
    finish_repeat_order(chat_id) if order.get("repeat_order") else send_payment_message(chat_id)


@bot.message_handler(func=lambda message: orders_db.get(message.chat.id, {}).get("waiting_delivery_service", False))
def handle_delivery_service(message):
    if message.text not in ("Яндекс", "Ozon", "5Post"): return
    order = orders_db.get(message.chat.id)
    if not order: return
    order["delivery_service"] = message.text; order["waiting_delivery_service"] = False; order["waiting_delivery_address"] = True
    bot.send_message(message.chat.id, "📍 Напишите вручную адрес, куда отправить заказ.\n\nМожно просто указать город и адрес выбранного ПВЗ 😊", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda message: orders_db.get(message.chat.id, {}).get("waiting_delivery_address", False))
def handle_delivery_address(message):
    chat_id = message.chat.id; order = orders_db.get(chat_id)
    if not order: return
    address = (message.text or "").strip()
    if not address: bot.send_message(chat_id, "Напишите, пожалуйста, адрес ещё раз 😊"); return
    order["delivery_address"] = address; order["waiting_delivery_address"] = False
    finish_repeat_order(chat_id) if order.get("repeat_order") else send_payment_message(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid(call):
    chat_id = call.message.chat.id; order = orders_db.get(chat_id)
    if not order: bot.answer_callback_query(call.id, "Заказ не найден."); return
    if order.get("paid_status") == "paid": bot.answer_callback_query(call.id, "Оплата уже отмечена."); return
    stock_ok, stock_error = decrement_stock(order)
    if not stock_ok:
        bot.answer_callback_query(call.id, "Не удалось подтвердить наличие товара.", show_alert=True)
        request_contact(chat_id, ("Не удалось связаться с системой остатков. " if stock_error == "Не удалось связаться с системой остатков." else "⚠️ Не удалось подтвердить наличие товара.\n\n") + CONTACT_TEXT, stock_error); return
    order["paid_status"] = "paid"; bot.answer_callback_query(call.id, "Спасибо!")
    try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except Exception as error: print("Не удалось убрать кнопки оплаты:", error)
    request_contact(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "wait_manager")
def wait_manager(call):
    chat_id = call.message.chat.id; order = orders_db.get(chat_id)
    if not order: bot.answer_callback_query(call.id, "Заказ не найден."); return
    order["waiting_manager"] = True; bot.answer_callback_query(call.id)
    try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except Exception as error: print("Не удалось убрать кнопки оплаты:", error)
    request_contact(chat_id)


@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    chat_id = message.chat.id; order = orders_db.get(chat_id)
    if not order: return
    order["phone"] = message.contact.phone_number; order["waiting_contact"] = False
    if order.get("repeat_order"):
        if order.get("needs_delivery"): start_delivery(chat_id)
        else: finish_repeat_order(chat_id)
        return
    if order.get("paid_status") or order.get("waiting_manager") or order.get("contact_required"): send_owner_notification(chat_id)
    if order.get("paid_status"): send_final_order_message(chat_id)
    elif order.get("waiting_manager"): bot.send_message(chat_id, "Хорошо 😊\n\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.", reply_markup=shop_keyboard())


@bot.message_handler(func=lambda message: message.text == "💬 Не отправлять номер, связаться в ТГ")
def no_phone(message):
    chat_id = message.chat.id; order = orders_db.get(chat_id)
    if not order: return
    order["waiting_contact"] = False; order["phone"] = None
    if order.get("repeat_order"):
        if order.get("needs_delivery"): start_delivery(chat_id)
        else: finish_repeat_order(chat_id)
        return
    if order.get("paid_status") or order.get("waiting_manager") or order.get("contact_required"): send_owner_notification(chat_id)
    if order.get("paid_status"): send_final_order_message(chat_id)
    elif order.get("waiting_manager"): bot.send_message(chat_id, "Хорошо 😊\n\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.", reply_markup=shop_keyboard())


@bot.message_handler(func=lambda message: message.text == "🛍 Магазин")
def open_shop(message): return


if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling(skip_pending=True)
