import json
import urllib.parse
import urllib.request
from telebot import types
import telebot

from config import BOT_TOKEN


# =========================
# НАСТРОЙКИ
# =========================

YOUR_TELEGRAM_ID = 5219493908

WEB_APP_URL = "https://likagratrow.github.io/Shop/"

SHEET_ID = "1FcetqNVvNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk"

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
        custom_button,
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
            "Не удалось получить данные заказа. "
            "Попробуйте оформить заказ ещё раз.",
            reply_markup=shop_keyboard()
        )

        return

    items = str(
        data.get(
            "items",
            ""
        )
    ).strip()

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

    if needs_delivery:
        options = load_delivery_options()

        if not options:
            print(
                "Не удалось загрузить варианты доставки."
            )

            bot.send_message(
                chat_id,
                "Не удалось загрузить варианты доставки. "
                "Попробуйте оформить заказ ещё раз.",
                reply_markup=shop_keyboard()
            )

            return

        orders_db[chat_id][
            "delivery_options"
        ] = options

        orders_db[chat_id][
            "waiting_delivery"
        ] = True

        bot.send_message(
            chat_id,
            "🚚 Как вам доставить заказ?",
            reply_markup=delivery_keyboard(
                options
            )
        )

        return

    send_payment_message(
        chat_id
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

    options = order.get(
        "delivery_options",
        []
    )

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
            "Пожалуйста, выберите один "
            "из вариантов доставки кнопкой ниже.",
            reply_markup=delivery_keyboard(
                options
            )
        )

        return

    order["delivery_id"] = (
        selected_option["id"]
    )

    order["delivery_title"] = (
        selected_option["title"]
    )

    order["delivery_price"] = (
        selected_option["price"]
    )

    order["waiting_delivery"] = False

    product_total = order.get(
        "product_total",
        0
    )

    delivery_price = selected_option[
        "price"
    ]

    if delivery_price is not None:
        order["total"] = (
            product_total
            + delivery_price
        )

    else:
        order["total"] = product_total

    if selected_option["id"] == "russia":

        order["waiting_delivery_service"] = True

        bot.send_message(
            chat_id,
            "📦 Выберите службу доставки:",
            reply_markup=delivery_service_keyboard()
        )

        return

    address_prompt = get_delivery_address_prompt(
        selected_option["id"]
    )

    if address_prompt:
        order["waiting_delivery_address"] = True

        bot.send_message(
            chat_id,
            address_prompt,
            reply_markup=types.ReplyKeyboardRemove()
        )

        return

    bot.send_message(
        chat_id,
        "Способ доставки выбран 👍",
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

    if not message.text:
        bot.send_message(
            chat_id,
            "Напишите, пожалуйста, данные для доставки "
            "обычным текстом 😊"
        )

        return

    delivery_address = message.text.strip()

    if not delivery_address:
        bot.send_message(
            chat_id,
            "Кажется, здесь ничего не получилось написать 😊\n\n"
            "Пожалуйста, отправьте адрес или страну "
            "ещё раз."
        )

        return

    order["delivery_address"] = delivery_address

    order["waiting_delivery_address"] = False

    bot.send_message(
        chat_id,
        "Записал 👍\n\n"
        "Теперь всё необходимое для заказа есть.",
        reply_markup=types.ReplyKeyboardRemove()
    )

    send_payment_message(
        chat_id
    )


# =========================
# УДАЛЕНИЕ КНОПОК ИЗ СООБЩЕНИЯ
# =========================

def remove_payment_buttons(call):
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )

    except Exception as error:
        print(
            "Не удалось убрать кнопки оплаты:",
            error
        )


# =========================
# КЛИЕНТ НАЖАЛ «Я ОПЛАТИЛ»
# =========================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "paid"
)
def handle_paid(call):
    chat_id = call.message.chat.id

    remove_payment_buttons(
        call
    )

    bot.answer_callback_query(
        call.id
    )

    order = orders_db.get(
        chat_id
    )

    if not order:
        bot.send_message(
            chat_id,
            "Не удалось найти ваш заказ. "
            "Пожалуйста, оформите его ещё раз.",
            reply_markup=shop_keyboard()
        )

        return

    order["paid_status"] = "paid"

    order["waiting_manager"] = False

    order["waiting_contact"] = True

    bot.send_message(
        chat_id,
        "Спасибо! Для завершения оформления заказа "
        "отправьте номер телефона или, если "
        "удобнее, свяжемся через Telegram",
        reply_markup=contact_keyboard()
    )


# =========================
# КЛИЕНТ НАЖАЛ
# «ПОДОЖДУ МЕНЕДЖЕРА»
# =========================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "wait_manager"
)
def handle_wait_manager(call):
    chat_id = call.message.chat.id

    remove_payment_buttons(
        call
    )

    bot.answer_callback_query(
        call.id
    )

    order = orders_db.get(
        chat_id
    )

    if not order:
        bot.send_message(
            chat_id,
            "Не удалось найти ваш заказ. "
            "Пожалуйста, оформите его ещё раз.",
            reply_markup=shop_keyboard()
        )

        return

    order["paid_status"] = "waiting_manager"

    order["waiting_manager"] = True

    order["waiting_contact"] = True

    bot.send_message(
        chat_id,
        "Хорошо)\n\n"
        "Менеджер свяжется с вами в рабочее время:\n"
        "Пн–Пт, 10:00–18:00 "
        "(Екатеринбург).\n\n"
        "Для связи отправьте номер телефона или, "
        "если удобнее, свяжемся через Telegram",
        reply_markup=contact_keyboard()
    )


# =========================
# КЛИЕНТ НЕ ХОЧЕТ ДАВАТЬ ТЕЛЕФОН
# =========================

@bot.message_handler(
    func=lambda message:
    message.text ==
    "💬 Не отправлять номер, связаться в ТГ"
)
def handle_no_phone(message):
    chat_id = message.chat.id

    order = orders_db.get(
        chat_id
    )

    if not order:
        bot.send_message(
            chat_id,
            "Не удалось найти ваш заказ. "
            "Пожалуйста, оформите его ещё раз.",
            reply_markup=shop_keyboard()
        )

        return

    current_username = (
        message.from_user.username
        if message.from_user
        else None
    )

    order["username"] = (
        current_username
    )

    order["waiting_contact"] = True

    if not current_username:
        bot.send_message(
            chat_id,
            "Похоже, у вас сейчас нет активного "
            "Telegram-ника для связи.\n\n"
            "Пожалуйста, отправьте номер телефона.",
            reply_markup=contact_keyboard()
        )

        return

    finalize_order(
        chat_id
    )


# =========================
# НОРМАЛИЗАЦИЯ ТЕЛЕФОНА
# =========================

def normalize_phone(phone):
    if not phone:
        return None

    phone = str(
        phone
    ).strip()

    cleaned = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if (
        cleaned.startswith("7")
        and len(cleaned) == 11
    ):
        cleaned = "+" + cleaned

    elif (
        cleaned.startswith("8")
        and len(cleaned) == 11
    ):
        cleaned = (
            "+7"
            + cleaned[1:]
        )

    elif cleaned.startswith("+"):
        pass

    return cleaned


# =========================
# ПОЛУЧЕНИЕ ТЕЛЕФОНА
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
        bot.send_message(
            chat_id,
            "Не удалось найти ваш заказ. "
            "Пожалуйста, оформите его ещё раз.",
            reply_markup=shop_keyboard()
        )

        return

    order["phone"] = normalize_phone(
        message.contact.phone_number
    )

    order["username"] = (
        message.from_user.username
        if message.from_user
        else None
    )

    order["waiting_contact"] = False

    finalize_order(
        chat_id
    )


# =========================
# ПРОВЕРКА АКТИВНОГО USERNAME
# =========================

def verify_current_username(user_id):
    try:
        user_chat = bot.get_chat(
            user_id
        )

        username = getattr(
            user_chat,
            "username",
            None
        )

        if username:
            return username

        return None

    except Exception as error:
        print(
            "Ошибка проверки username:",
            error
        )

        return None


# =========================
# ФИНАЛИЗАЦИЯ ЗАКАЗА
# =========================

def finalize_order(chat_id):
    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    if order.get("completed"):
        return

    user_id = order.get(
        "user_id",
        chat_id
    )

    verified_username = (
        verify_current_username(
            user_id
        )
    )

    if verified_username:
        order["username"] = (
            verified_username
        )

    else:
        order["username"] = None

    if not order.get("username"):

        if order.get("phone"):
            send_owner_notification(
                chat_id
            )

            return

        order["waiting_contact"] = True

        bot.send_message(
            chat_id,
            "Похоже, ваш Telegram-ник больше "
            "не активен для связи.\n\n"
            "Чтобы мы точно смогли связаться с вами "
            "по заказу, пожалуйста, отправьте номер "
            "телефона.",
            reply_markup=contact_keyboard()
        )

        return

    send_owner_notification(
        chat_id
    )


# =========================
# ФИНАЛЬНОЕ УВЕДОМЛЕНИЕ ВЛАДЕЛЬЦУ
# =========================

def send_owner_notification(chat_id):
    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    if order.get("completed"):
        return

    user_id = order.get(
        "user_id",
        chat_id
    )

    verified_username = (
        verify_current_username(
            user_id
        )
    )

    if verified_username:
        order["username"] = (
            verified_username
        )

    else:
        order["username"] = None

    if (
        not order.get("username")
        and not order.get("phone")
    ):
        order["waiting_contact"] = True

        bot.send_message(
            chat_id,
            "Похоже, ваш Telegram-ник больше "
            "не активен для связи, а номер телефона "
            "ещё не указан.\n\n"
            "Пожалуйста, отправьте номер телефона.",
            reply_markup=contact_keyboard()
        )

        return

    first_name = order.get(
        "first_name",
        "не указано"
    )

    username = order.get(
        "username"
    )

    phone = order.get(
        "phone"
    )

    user_id = order.get(
        "user_id",
        chat_id
    )

    if username:
        username_text = (
            f"@{username}"
        )

    else:
        username_text = "нет ника"

    if phone:
        phone_text = phone

    else:
        phone_text = "не предоставлен"

    if order.get(
        "paid_status"
    ) == "paid":

        status_text = (
            "💳 Клиент отметил, что оплатил.\n"
            "⚠️ Проверь поступление денег и выпиши чек."
        )

    else:

        status_text = (
            "⚠️ ЗАПРОСИТЬ ОПЛАТУ\n"
            "Клиент ожидает диалога "
            "перед оплатой."
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

    if delivery_title:

        if delivery_price is None:

            delivery_text = (
                f"🚚 Доставка: {delivery_title} "
                "(стоимость по согласованию)"
            )

        else:

            delivery_text = (
                f"🚚 Доставка: {delivery_title} — "
                f"{format_price(delivery_price)}"
            )

    else:

        delivery_text = None

    owner_text = (
        "🆕 НОВЫЙ ЗАКАЗ\n\n"

        f"👤 Покупатель: {first_name}\n"

        f"💬 Telegram: {username_text}\n"

        f"🆔 Telegram ID: {user_id}\n"

        f"📱 Телефон: {phone_text}\n\n"

        "🛒 Заказ:\n"
        f"{order.get('items', '')}\n\n"

        f"💰 Товары: "
        f"{format_price(order.get('product_total', 0))}\n"
    )

    if delivery_text:
        owner_text += (
            f"{delivery_text}\n"
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
            f"<b>{format_price(order.get('product_total', 0))}</b> + "
            "доставка по согласованию\n\n"
        )

    else:

        owner_text += (
            f"💰 Итого: "
            f"<b>{format_price(order.get('total', 0))}</b>\n\n"
        )

    owner_text += (
        f"{status_text}"
    )

    bot.send_message(
        YOUR_TELEGRAM_ID,
        owner_text,
        parse_mode="HTML"
    )

    order["completed"] = True

    order["waiting_contact"] = False

    if order.get("delivery_id") == "courier_ekb":

        final_message = (
            "Спасибо!\n\n"
            "Всё-всё записал и передал менеджеру) "
            "Сборка заказа обычно занимает один рабочий день, "
            "затем мы с вами свяжемся и обрадуем, "
            "что готовы организовать доставку. "
            "Спасибо за заказ!"
        )

    else:

        final_message = (
            "Спасибо!\n\n"
            "Всё-всё записал и передал менеджеру) "
            "Сборка заказа обычно занимает один рабочий день, "
            "затем мы с вами свяжемся и обрадуем, "
            "что можно забрать (или что он отправлен). "
            "Спасибо за заказ!"
        )

    bot.send_message(
        chat_id,
        final_message,
        reply_markup=shop_keyboard()
    )


# =========================
# ОБРАБОТКА ТЕКСТА,
# КОГДА ЖДЁМ КОНТАКТ
# =========================

@bot.message_handler(
    func=lambda message:
    orders_db.get(
        message.chat.id,
        {}
    ).get(
        "waiting_contact",
        False
    )
)
def handle_text_while_waiting_contact(message):
    chat_id = message.chat.id

    order = orders_db.get(
        chat_id
    )

    if not order:
        return

    if message.text:

        current_username = (
            message.from_user.username
            if message.from_user
            else None
        )

        order["username"] = (
            current_username
        )

        if not current_username:

            bot.send_message(
                chat_id,
                "Сейчас у вас нет активного "
                "Telegram-ника для связи.\n\n"
                "Пожалуйста, отправьте номер телефона "
                "кнопкой ниже.",
                reply_markup=contact_keyboard()
            )

            return

        finalize_order(
            chat_id
        )


# =========================
# ЗАПУСК БОТА
# =========================

print("Бот запущен...")

bot.infinity_polling()
