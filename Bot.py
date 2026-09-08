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

    if not isinstance(products, list) or not products:
        print(
            "Ошибка списания остатков: пустой или некорректный список products",
            products
        )
        return False, "В заказе отсутствует список товаров."

    normalized_products = []

    for product in products:
        if not isinstance(product, dict):
            print(
                "Ошибка списания остатков: некорректный товар",
                product
            )
            return False, "Некорректные данные товара."

        product_id = str(
            product.get("id", "")
        ).strip()

        quantity = product.get(
            "quantity"
        )

        if not product_id:
            print(
                "Ошибка списания остатков: у товара отсутствует id",
                product
            )
            return False, "Некорректные данные товара."

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            print(
                "Ошибка списания остатков: некорректное количество",
                product
            )
            return False, "Некорректное количество товара."

        if quantity < 1:
            print(
                "Ошибка списания остатков: количество меньше 1",
                product
            )
            return False, "Некорректное количество товара."

        normalized_products.append(
            {
                "id": product_id,
                "quantity": quantity
            }
        )

    payload = json.dumps(
        {
            "action": "check_and_decrement",
            "items": normalized_products
        },
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
        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:
            text = response.read().decode(
                "utf-8"
            )

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            print(
                "Ошибка списания остатков: некорректный ответ API:",
                text
            )
            return False, "Система остатков вернула некорректный ответ."

        print(
            "Ответ системы остатков:",
            result
        )

        if result.get("ok"):
            return True, None

        return False, result.get(
            "error",
            "Не удалось обновить остатки."
        )

    except urllib.error.HTTPError as error:
        try:
            error_text = error.read().decode(
                "utf-8",
                errors="replace"
            )
        except Exception:
            error_text = ""

        print(
            "HTTP-ошибка списания остатков:",
            error.code,
            error_text
        )

        return False, "Не удалось связаться с системой остатков."

    except urllib.error.URLError as error:
        print(
            "Ошибка соединения с системой остатков:",
            error.reason
        )

        return False, "Не удалось связаться с системой остатков."

    except Exception as error:
        print(
            "Ошибка списания остатков:",
            repr(error)
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

    keyboard.row(
        types.InlineKeyboardButton(
            "💳 Я оплатил",
            callback_data="paid"
        ),
        types.InlineKeyboardButton(
            "⏳ Подожду менеджера",
            callback_data="wait_manager"
        )
    )

    bot.send_message(
        chat_id,
        customer_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================
# КОМАНДА /START
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! 😊\n\n"
        "Здесь можно посмотреть товары, "
        "записаться на мастер-класс или "
        "связаться с нами.",
        reply_markup=shop_keyboard()
    )


# =========================
# WEB APP DATA
# =========================

@bot.message_handler(content_types=["web_app_data"])
def handle_web_app_data(message):
    print(
        "RAW WEB APP DATA:",
        message.web_app_data.data
    )

    try:
        data = json.loads(
            message.web_app_data.data
        )
    except json.JSONDecodeError:
        bot.send_message(
            message.chat.id,
            "Не удалось прочитать заказ. Попробуйте ещё раз."
        )
        return

    products = data.get(
        "products",
        []
    )

    orders_db[message.chat.id] = {
        "items": data.get("items", ""),
        "products": products,
        "product_total": data.get("total", 0),
        "total": data.get("total", 0),
        "needs_delivery": data.get("needs_delivery", False)
    }

    order = orders_db[message.chat.id]

    if order.get("needs_delivery"):
        options = load_delivery_options()

        if not options:
            bot.send_message(
                message.chat.id,
                "Не удалось загрузить варианты доставки. "
                "Попробуйте ещё раз позже."
            )
            return

        bot.send_message(
            message.chat.id,
            "🚚 Выберите способ доставки:",
            reply_markup=delivery_keyboard(options)
        )

    else:
        send_payment_message(message.chat.id)


# =========================
# ОПЛАТА
# =========================

@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid(call):
    order = orders_db.get(
        call.message.chat.id
    )

    if not order:
        bot.answer_callback_query(
            call.id,
            "Заказ не найден."
        )
        return

    if order.get("paid"):
        bot.answer_callback_query(
            call.id,
            "Оплата уже отмечена."
        )
        return

    stock_ok, stock_error = decrement_stock(
        order
    )

    if not stock_ok:
        bot.answer_callback_query(
            call.id,
            "Не удалось подтвердить наличие товара.",
            show_alert=True
        )
        bot.send_message(
            call.message.chat.id,
            "⚠️ Не удалось подтвердить наличие товара.\n\n"
            f"Причина: {stock_error}\n\n"
            "Оплата пока не отмечена."
        )
        return

    order["paid"] = True

    bot.answer_callback_query(
        call.id,
        "Оплата отмечена!"
    )

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None
    )

    bot.send_message(
        call.message.chat.id,
        "Спасибо! 💳\n\n"
        "Оплата отмечена. Заказ принят в работу."
    )


# =========================
# МЕНЕДЖЕР
# =========================

@bot.callback_query_handler(func=lambda call: call.data == "wait_manager")
def wait_manager(call):
    order = orders_db.get(
        call.message.chat.id
    )

    if not order:
        bot.answer_callback_query(
            call.id,
            "Заказ не найден."
        )
        return

    bot.answer_callback_query(
        call.id,
        "Хорошо!"
    )

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None
    )

    bot.send_message(
        call.message.chat.id,
        "Хорошо 😊\n\n"
        "Менеджер свяжется с вами в рабочее время."
    )


# =========================
# ДОСТАВКА
# =========================

@bot.message_handler(func=lambda message: message.text == "📅 Записаться")
def booking(message):
    bot.send_message(
        message.chat.id,
        "Запись на мастер-классы пока оформляется "
        "через менеджера 😊"
    )


@bot.message_handler(func=lambda message: message.text == "🧵 Индивидуальный заказ")
def custom_order(message):
    bot.send_message(
        message.chat.id,
        "Напишите, что вы хотите заказать, "
        "и мы свяжемся с вами 😊"
    )


@bot.message_handler(func=lambda message: message.text == "💬 Обратная связь")
def feedback(message):
    bot.send_message(
        message.chat.id,
        "Напишите ваше сообщение следующим сообщением 😊"
    )


# =========================
# КОНТАКТНЫЕ ДАННЫЕ
# =========================

@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    orders_db.setdefault(
        message.chat.id,
        {}
    )["phone"] = message.contact.phone_number

    bot.send_message(
        message.chat.id,
        "Спасибо! Номер получил 😊",
        reply_markup=shop_keyboard()
    )


# =========================
# ДОСТАВКА: ВЫБОР
# =========================

@bot.message_handler(func=lambda message: orders_db.get(message.chat.id, {}).get("needs_delivery") and not orders_db.get(message.chat.id, {}).get("delivery_title"))
def handle_delivery_choice(message):
    options = load_delivery_options()

    selected = None

    for option in options:
        if message.text.startswith(option["title"] + " "):
            selected = option
            break

    if not selected:
        return

    order = orders_db.get(
        message.chat.id
    )

    order["delivery_id"] = selected["id"]
    order["delivery_title"] = selected["title"]
    order["delivery_price"] = selected["price"]

    prompt = get_delivery_address_prompt(
        selected["id"]
    )

    if prompt:
        bot.send_message(
            message.chat.id,
            prompt,
            reply_markup=types.ReplyKeyboardRemove()
        )
        order["waiting_for_delivery_address"] = True
        return

    bot.send_message(
        message.chat.id,
        "📦 Выберите службу доставки:",
        reply_markup=delivery_service_keyboard()
    )

    order["waiting_for_delivery_service"] = True


# =========================
# АДРЕС ДОСТАВКИ
# =========================

@bot.message_handler(func=lambda message: orders_db.get(message.chat.id, {}).get("waiting_for_delivery_address"))
def handle_delivery_address(message):
    order = orders_db.get(
        message.chat.id
    )

    order["delivery_address"] = message.text.strip()
    order["waiting_for_delivery_address"] = False

    if order.get("delivery_id") == "russia":
        bot.send_message(
            message.chat.id,
            "📦 Выберите службу доставки:",
            reply_markup=delivery_service_keyboard()
        )
        order["waiting_for_delivery_service"] = True
        return

    send_payment_message(
        message.chat.id
    )


# =========================
# СЛУЖБА ДОСТАВКИ
# =========================

@bot.message_handler(func=lambda message: orders_db.get(message.chat.id, {}).get("waiting_for_delivery_service"))
def handle_delivery_service(message):
    if message.text not in (
        "Яндекс",
        "Ozon",
        "5Post"
    ):
        return

    order = orders_db.get(
        message.chat.id
    )

    order["delivery_service"] = message.text
    order["waiting_for_delivery_service"] = False

    send_payment_message(
        message.chat.id
    )


# =========================
# ОТМЕНА / МЕНЮ
# =========================

@bot.message_handler(func=lambda message: message.text == "🛍 Магазин")
def open_shop(message):
    bot.send_message(
        message.chat.id,
        "Открываю магазин 🛍",
        reply_markup=shop_keyboard()
    )


# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling(skip_pending=True)
