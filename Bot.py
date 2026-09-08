import json
import urllib.parse
import urllib.request
from telebot import types
import telebot

from config import BOT_TOKEN

try:
    from config import STOCK_API_SECRET
except ImportError:
    STOCK_API_SECRET = ""


# =========================
# НАСТРОЙКИ
# =========================

YOUR_TELEGRAM_ID = 5219493908

WEB_APP_URL = "https://likagratrow.github.io/Shop/"

SHEET_ID = "1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk"

STOCK_API_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbwwkQeC1U82T0LoYv9umYrc-pmeD0KSZP0IOWAtEvWrKGagUNPJeoUvtIyviQF4-vfoTg"
    "/exec"
)

DELIVERY_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/gviz/tq"
    f"?sheet=%D0%94%D0%BE%D1%81%D1%82%D0%B0%D0%B2%D0%BA%D0%B0"
)

bot = telebot.TeleBot(BOT_TOKEN)


# =========================
# ДАННЫЕ ЗАКАЗОВ
# =========================

orders_db = {}


# =========================
# ОБЩАЯ КЛАВИАТУРА МЕНЮ
# =========================

def shop_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    shop_button = types.KeyboardButton(
        "🛍 Магазин",
        web_app=types.WebAppInfo(
            url=WEB_APP_URL
        )
    )

    booking_button = types.KeyboardButton(
        "📅 Записаться"
    )

    custom_button = types.KeyboardButton(
        "🧵 Индивидуальный заказ"
    )

    feedback_button = types.KeyboardButton(
        "💬 Обратная связь"
    )

    keyboard.row(
        shop_button,
        booking_button
    )

    keyboard.row(
        custom_button
    )

    keyboard.row(
        feedback_button
    )

    return keyboard


# =========================
# КЛАВИАТУРА КОНТАКТА
# =========================

def contact_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    phone_button = types.KeyboardButton(
        "📱 Отправить номер телефона",
        request_contact=True
    )

    no_phone_button = types.KeyboardButton(
        "💬 Не отправлять номер, связаться в ТГ"
    )

    keyboard.row(phone_button)
    keyboard.row(no_phone_button)

    return keyboard


# =========================
# ЗАГРУЗКА ДОСТАВКИ ИЗ GOOGLE SHEETS
# =========================

def load_delivery_options():
    options = []

    try:
        with urllib.request.urlopen(
            DELIVERY_SHEET_URL,
            timeout=10
        ) as response:

            text = response.read().decode(
                "utf-8"
            )

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "Не удалось найти JSON в ответе Google Sheets"
            )

        data = json.loads(
            text[start:end + 1]
        )

        rows = data.get(
            "table",
            {}
        ).get(
            "rows",
            []
        )

        for row in rows:
            cells = row.get(
                "c",
                []
            )

            values = []

            for cell in cells:
                if cell is None:
                    values.append("")
                else:
                    values.append(
                        str(
                            cell.get(
                                "v",
                                ""
                            )
                        ).strip()
                    )

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
                        price_raw
                        .replace(" ", "")
                        .replace(",", ".")
                        .replace("₽", "")
                    )

                    if price.is_integer():
                        price = int(price)

                except Exception:
                    price = None

            options.append(
                {
                    "id": delivery_id,
                    "title": title,
                    "price": price
                }
            )

        return options

    except Exception as error:
        print(
            "Ошибка загрузки доставки:",
            error
        )

        return []


# =========================
# КЛАВИАТУРА ДОСТАВКИ
# =========================

def delivery_keyboard(options):
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    for option in options:
        if option["price"] is None:
            price_text = "договорная"
        else:
            price_text = (
                f"{option['price']:,} ₽"
                .replace(",", " ")
            )

        button_text = (
            f"{option['title']} "
            f"({price_text})"
        )

        keyboard.row(
            types.KeyboardButton(
                button_text
            )
        )

    return keyboard


# =========================
# КЛАВИАТУРА СЛУЖБЫ ДОСТАВКИ
# =========================

def delivery_service_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    keyboard.row(
        types.KeyboardButton(
            "Яндекс"
        )
    )

    keyboard.row(
        types.KeyboardButton(
            "Ozon"
        )
    )

    keyboard.row(
        types.KeyboardButton(
            "5Post"
        )
    )

    return keyboard


# =========================
# ФОРМАТ ЦЕНЫ
# =========================

def format_price(value):
    try:
        return (
            f"{int(value):,}"
            .replace(",", " ")
            + " ₽"
        )

    except Exception:
        return f"{value} ₽"


# =========================
# ПРОВЕРКА И СПИСАНИЕ ОСТАТКОВ
# =========================

def decrement_stock(order):
    products = order.get(
        "products",
        []
    )

    if not products:
        return False, "В заказе отсутствует список товаров."

    if not STOCK_API_SECRET:
        return False, "Не настроен секрет для управления остатками."

    payload = json.dumps(
        {
            "secret": STOCK_API_SECRET,
            "action": "check_and_decrement",
            "items": products
        },
        ensure_ascii=False
    ).encode("utf-8")

    request = urllib.request.Request(
        STOCK_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:
            text = response.read().decode(
                "utf-8"
            )

        result = json.loads(text)

        if result.get("ok"):
            return True, None

        return False, result.get(
            "error",
            "Не удалось обновить остатки."
        )

    except Exception as error:
        print(
            "Ошибка списания остатков:",
            error
        )

        return False, "Не удалось связаться с системой остатков."


# =========================
# ОПРЕДЕЛЕНИЕ, ЧТО СПРОСИТЬ
# =========================

def get_delivery_address_prompt(delivery_id):
    if delivery_id == "courier_ekb":
        return (
            "📍 Теперь напишите вручную адрес, "
            "куда привезти заказ курьером.\n\n"
            "Нужен адрес квартиры: "
            "улица, дом, квартира 😊"
        )

    if delivery_id == "russia":
        return None

    if delivery_id == "abroad":
        return (
            "🌍 Теперь напишите вручную страну, "
            "в которую отправляем заказ.\n\n"
            "Дальше детали доставки мы согласуем с вами отдельно 😊"
        )

    return None


# =========================
# ОПЛАТА
# =========================

def send_payment_message(chat_id):
    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    items = order.get(
        "items",
        ""
    )

    product_total = order.get(
        "product_total",
        order.get("total", 0)
    )

    delivery_title = order.get(
        "delivery_title"
    )

    delivery_price = order.get(
        "delivery_price"
    )

    delivery_service = order.get(
        "delivery_service"
    )

    total = order.get(
        "total",
        product_total
    )

    if delivery_title:
        if delivery_price is None:
            delivery_line = (
                f"🚚 Доставка: {delivery_title} "
                "(стоимость по согласованию)"
            )
        else:
            delivery_line = (
                f"🚚 Доставка: {delivery_title} — "
                f"{format_price(delivery_price)}"
            )
    else:
        delivery_line = None

    customer_text = (
        "Ваш заказ:\n\n"
        f"{items}\n\n"
        f"💰 Товары: {format_price(product_total)}\n"
    )

    if delivery_line:
        customer_text += (
            f"{delivery_line}\n"
        )

    if delivery_service:
        customer_text += (
            f"📦 Служба доставки: "
            f"{delivery_service}\n"
        )

    delivery_address = order.get(
        "delivery_address"
    )

    if delivery_address:
        customer_text += (
            f"📍 Куда доставить: "
            f"{delivery_address}\n"
        )

    customer_text += "\n"

    if delivery_price is None and delivery_title:
        customer_text += (
            f"💰 Итого: "
            f"<b>{format_price(product_total)}</b> + "
            "доставка по согласованию\n\n"
        )
    else:
        customer_text += (
            f"💰 Итого: "
            f"<b>{format_price(total)}</b>\n\n"
        )

    if delivery_price is None and delivery_title:
        customer_text += (
            "📦 Стоимость доставки будет "
            "согласована с менеджером.\n\n"
        )

    customer_text += (
        "💳 Оплата переводом на Сбербанк:\n"
        "📱 +79089147913\n"
        "👤 Получатель: Лия П.\n\n"
        "📦 Заказ будет собран после оплаты.\n\n"
        "Вы можете перевести оплату сейчас "
        "или дождаться связи с менеджером "
        "в рабочее время:\n"
        "Пн–Пт, 10:00–18:00 "
        "(Екатеринбург)."
    )

    keyboard = types.InlineKeyboardMarkup()

    paid_button = types.InlineKeyboardButton(
        "💳 Я оплатил",
        callback_data="paid"
    )

    manager_button = types.InlineKeyboardButton(
        "⏳ Подожду менеджера",
        callback_data="wait_manager"
    )

    keyboard.row(
        paid_button
    )

    keyboard.row(
        manager_button
    )

    bot.send_message(
        chat_id,
        customer_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================
# START
# =========================

@bot.message_handler(
    commands=["start"]
)
def start(message):
    orders_db[
        message.chat.id
    ] = {}

    bot.send_message(
        message.chat.id,
        "Добро пожаловать в «Странные Вещи»\n\n"
        "Выберите, что хотите сделать.",
        reply_markup=shop_keyboard()
    )


# =========================
# КНОПКА «ЗАПИСАТЬСЯ»
# =========================

@bot.message_handler(
    func=lambda message:
    message.text == "📅 Записаться"
)
def handle_booking(message):
    bot.send_message(
        message.chat.id,
        "Записаться на МК или Диоген можно по адресу:\n"
        "https://dikidi.ru/2143045",
        reply_markup=shop_keyboard()
    )


# =========================
# КНОПКА «ИНДИВИДУАЛЬНЫЙ ЗАКАЗ»
# =========================

@bot.message_handler(
    func=lambda message:
    message.text == "🧵 Индивидуальный заказ"
)
def handle_custom_order(message):
    bot.send_message(
        message.chat.id,
        "Индивидуальные заказы пока принимаем "
        "вручную.\n\n"
        "Напишите, что хотите сделать, "
        "и мы обсудим детали.",
        reply_markup=shop_keyboard()
    )


# =========================
# КНОПКА «ОБРАТНАЯ СВЯЗЬ»
# =========================

@bot.message_handler(
    func=lambda message:
    message.text == "💬 Обратная связь"
)
def handle_feedback(message):
    bot.send_message(
        message.chat.id,
        "Расскажите, что вы хотели бы нам сказать 😊",
        reply_markup=shop_keyboard()
    )


# =========================
# ДАННЫЕ ИЗ MINI APP
# =========================

@bot.message_handler(
    content_types=["web_app_data"]
)
def handle_web_app_data(message):
    chat_id = message.chat.id

    try:
        bot.delete_message(
            chat_id,
            message.message_id
        )

    except Exception as delete_error:
        print(
            "Не удалось удалить техническое сообщение:",
            delete_error
        )

    try:
        data = json.loads(
            message.web_app_data.data
        )

    except Exception as error:
        print(
            "Ошибка разбора данных Mini App:",
            error
        )

        bot.send_message(
            chat_id,
            "Извините, бот еще маленький и иногда теряет нить разговора. К сожалению, он пропустил заказ мимо ушей( Не могли бы вы повторить его снова, пожалуйста 🥺",
            reply_markup=shop_keyboard()
        )

        return

    items = str(
        data.get(
            "items",
            ""
        )
    ).strip()

    products = data.get(
        "products",
        []
    )

    if not isinstance(products, list):
        products = []

    total = data.get(
        "total",
        0
    )

    needs_delivery = bool(
        data.get(
            "needs_delivery",
            False
        )
    )

    items = items.replace(
        ", ",
        "\n"
    )

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
        "username": (
            message.from_user.username
            if message.from_user
            else None
        ),
        "user_id": (
            message.from_user.id
            if message.from_user
            else chat_id
        ),
        "first_name": (
            message.from_user.first_name
            if message.from_user
            else ""
        ),
        "waiting_manager": False,
        "waiting_contact": False,
        "waiting_delivery": False,
        "waiting_delivery_service": False,
        "waiting_delivery_address": False,
        "completed": False
    }

    if not needs_delivery:
        send_payment_message(
            chat_id
        )
        return

    options = load_delivery_options()

    if not options:
        bot.send_message(
            chat_id,
            "Извините, не удалось загрузить варианты доставки. "
            "Пожалуйста, попробуйте оформить заказ ещё раз.",
            reply_markup=shop_keyboard()
        )
        return

    order = orders_db[chat_id]

    order["waiting_delivery"] = True

    bot.send_message(
        chat_id,
        "🚚 Как вам доставить заказ?",
        reply_markup=delivery_keyboard(options)
    )


# =========================
# ВЫБОР ДОСТАВКИ
# =========================

@bot.message_handler(
    func=lambda message:
    orders_db.get(
        message.chat.id,
        {}
    ).get(
        "waiting_delivery",
        False
    )
)
def handle_delivery(message):
    chat_id = message.chat.id

    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    options = load_delivery_options()

    selected_option = None

    for option in options:
        if option["price"] is None:
            price_text = "договорная"
        else:
            price_text = (
                f"{option['price']:,} ₽"
                .replace(",", " ")
            )

        expected_text = (
            f"{option['title']} "
            f"({price_text})"
        )

        if message.text == expected_text:
            selected_option = option
            break

    if not selected_option:
        bot.send_message(
            chat_id,
            "Пожалуйста, выберите вариант доставки "
            "одной из кнопок ниже.",
            reply_markup=delivery_keyboard(options)
        )
        return

    order["waiting_delivery"] = False
    order["delivery_id"] = selected_option["id"]
    order["delivery_title"] = selected_option["title"]
    order["delivery_price"] = selected_option["price"]

    product_total = order.get(
        "product_total",
        order.get("total", 0)
    )

    if selected_option["price"] is None:
        order["total"] = product_total
    else:
        order["total"] = (
            product_total
            + selected_option["price"]
        )

    if selected_option["id"] == "russia":
        order["waiting_delivery_service"] = True

        bot.send_message(
            chat_id,
            "📦 Выберите службу доставки:",
            reply_markup=delivery_service_keyboard()
        )

        return

    prompt = get_delivery_address_prompt(
        selected_option["id"]
    )

    if prompt:
        order["waiting_delivery_address"] = True

        bot.send_message(
            chat_id,
            prompt,
            reply_markup=types.ReplyKeyboardRemove()
        )

        return

    bot.send_message(
        chat_id,
        "Спасибо! 😊",
        reply_markup=types.ReplyKeyboardRemove()
    )

    send_payment_message(
        chat_id
    )


# =========================
# ВЫБОР СЛУЖБЫ ДОСТАВКИ
# =========================

@bot.message_handler(
    func=lambda message:
    orders_db.get(
        message.chat.id,
        {}
    ).get(
        "waiting_delivery_service",
        False
    )
)
def handle_delivery_service(message):
    chat_id = message.chat.id

    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    services = {
        "Яндекс": "Яндекс",
        "Ozon": "Ozon",
        "5Post": "5Post"
    }

    selected_service = services.get(
        message.text
    )

    if not selected_service:
        bot.send_message(
            chat_id,
            "Пожалуйста, выберите службу доставки "
            "одной из кнопок ниже.",
            reply_markup=delivery_service_keyboard()
        )

        return

    order["delivery_service"] = (
        selected_service
    )

    order["waiting_delivery_service"] = False
    order["waiting_delivery_address"] = True

    bot.send_message(
        chat_id,
        "📍 Отлично)\n\n"
        "Теперь напишите вручную адрес ПВЗ, "
        "куда отправить заказ.\n\n"
        "Можно просто указать город и адрес "
        "выбранного ПВЗ 😊",
        reply_markup=types.ReplyKeyboardRemove()
    )


# =========================
# АДРЕС / СТРАНА ДОСТАВКИ
# =========================

@bot.message_handler(
    func=lambda message:
    orders_db.get(
        message.chat.id,
        {}
    ).get(
        "waiting_delivery_address",
        False
    )
)
def handle_delivery_address(message):
    chat_id = message.chat.id

    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    address = (
        message.text or ""
    ).strip()

    if not address:
        bot.send_message(
            chat_id,
            "Напишите, пожалуйста, адрес ещё раз 😊"
        )
        return

    order["delivery_address"] = address
    order["waiting_delivery_address"] = False

    bot.send_message(
        chat_id,
        "Спасибо! 😊",
        reply_markup=types.ReplyKeyboardRemove()
    )

    send_payment_message(
        chat_id
    )


# =========================
# КНОПКА «Я ОПЛАТИЛ»
# =========================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "paid"
)
def paid(call):
    chat_id = call.message.chat.id

    order = orders_db.get(
        chat_id
    )

    if not order:
        bot.answer_callback_query(
            call.id,
            "Заказ не найден."
        )
        return

    if order.get("paid_status") == "paid":
        bot.answer_callback_query(
            call.id,
            "Заказ уже отмечен как оплаченный."
        )
        return

    stock_ok, stock_error = decrement_stock(
        order
    )

    if not stock_ok:
        bot.answer_callback_query(
            call.id,
            "Не удалось подтвердить заказ."
        )

        if stock_error == "Not enough stock":
            message_text = (
                "К сожалению, нужного количества товара уже нет в наличии. "
                "Пожалуйста, оформите заказ заново с актуальным количеством."
            )
        else:
            message_text = (
                "К сожалению, сейчас не удалось подтвердить наличие товара. "
                "Пожалуйста, попробуйте оформить заказ ещё раз."
            )

        bot.send_message(
            chat_id,
            message_text,
            reply_markup=shop_keyboard()
        )

        return

    order["paid_status"] = "paid"

    try:
        bot.edit_message_reply_markup(
            chat_id,
            call.message.message_id,
            reply_markup=None
        )
    except Exception as edit_error:
        print(
            "Не удалось убрать кнопки оплаты:",
            edit_error
        )

    bot.answer_callback_query(
        call.id,
        "Спасибо!"
    )

    bot.send_message(
        chat_id,
        "Спасибо! 😊\n\n"
        "Всё-всё записал и передал менеджеру)\n"
        "Сборка заказа обычно занимает один рабочий день, "
        "затем мы с вами свяжемся и обрадуем, "
        "что можно забрать (или что он отправлен).\n"
        "Спасибо за заказ!",
        reply_markup=shop_keyboard()
    )

    send_owner_notification(
        chat_id
    )


# =========================
# КНОПКА «ПОДОЖДУ МЕНЕДЖЕРА»
# =========================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "wait_manager"
)
def wait_manager(call):
    chat_id = call.message.chat.id

    order = orders_db.get(
        chat_id
    )

    if not order:
        bot.answer_callback_query(
            call.id,
            "Заказ не найден."
        )
        return

    order["waiting_manager"] = True

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        chat_id,
        "Хорошо 😊\n\n"
        "Менеджер свяжется с вами в рабочее время.\n"
        "Пн–Пт, 10:00–18:00 (Екатеринбург).",
        reply_markup=shop_keyboard()
    )

    send_owner_notification(
        chat_id
    )


# =========================
# КОНТАКТНЫЕ ДАННЫЕ
# =========================

@bot.message_handler(
    content_types=["contact"]
)
def handle_contact(message):
    chat_id = message.chat.id

    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    phone = message.contact.phone_number

    order["phone"] = phone
    order["waiting_contact"] = False

    bot.send_message(
        chat_id,
        "Спасибо! 😊",
        reply_markup=types.ReplyKeyboardRemove()
    )

    send_owner_notification(
        chat_id
    )


# =========================
# НЕ ОТПРАВЛЯТЬ НОМЕР
# =========================

@bot.message_handler(
    func=lambda message:
    message.text == "💬 Не отправлять номер, связаться в ТГ"
)
def no_phone(message):
    chat_id = message.chat.id
    
    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    order["waiting_contact"] = False
    order["phone"] = None

    bot.send_message(
        chat_id,
        "Хорошо 😊 Менеджер свяжется с вами в Telegram.",
        reply_markup=types.ReplyKeyboardRemove()
    )

    send_owner_notification(
        chat_id
    )


# =========================
# ФИНАЛЬНОЕ СООБЩЕНИЕ ВЛАДЕЛЬЦУ
# =========================

def send_owner_notification(chat_id):
    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    if order.get(
        "completed"
    ):
        return

    if not order.get(
        "paid_status"
    ) and not order.get(
        "waiting_manager"
    ):
        return

    order["completed"] = True

    username = order.get(
        "username"
    )

    first_name = order.get(
        "first_name"
    ) or ""

    phone = order.get(
        "phone"
    )

    items = order.get(
        "items",
        ""
    )

    product_total = order.get(
        "product_total",
        order.get("total", 0)
    )

    delivery_title = order.get(
        "delivery_title"
    )

    delivery_price = order.get(
        "delivery_price"
    )

    delivery_service = order.get(
        "delivery_service"
    )

    delivery_address = order.get(
        "delivery_address"
    )

    total = order.get(
        "total",
        product_total
    )

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
        owner_text += (
            f"📦 Служба доставки: "
            f"{delivery_service}\n"
        )

    if delivery_address:
        owner_text += (
            f"📍 Куда доставить: "
            f"{delivery_address}\n"
        )

    owner_text += "\n"

    if delivery_price is None and delivery_title:
        owner_text += (
            f"💰 Итого: "
            f"<b>{format_price(product_total)}</b> + "
            "доставка по согласованию\n"
        )
    else:
        owner_text += (
            f"💰 Итого: "
            f"<b>{format_price(total)}</b>\n"
        )

    owner_text += "\n"

    owner_text += (
        f"👤 Клиент: {first_name}\n"
    )

    if username:
        owner_text += (
            f"💬 Telegram: @{username}\n"
        )

    if phone:
        owner_text += (
            f"📱 Телефон: {phone}\n"
        )
    else:
        owner_text += (
            "📱 Телефон: не предоставлен\n"
        )

    if order.get(
        "waiting_manager"
    ):
        owner_text += (
            "\n⏳ Клиент ожидает диалога "
            "перед оплатой."
        )
    else:
        owner_text += (
            "\n💳 Клиент подтвердил оплату."
        )

    bot.send_message(
        YOUR_TELEGRAM_ID,
        owner_text,
        parse_mode="HTML"
    )


# =========================
# ЗАПУСК
# =========================

print("Бот запущен...")
bot.infinity_polling()