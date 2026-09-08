"""Логика кнопки «🧵 Индивидуальный заказ»."""

INDIVIDUAL_ORDER_PROMPT = "Опишите, что бы вы хотели заказать?"
MEDIA_PROMPT = "Есть ли у вас картинки, наброски или референсы?"
CONTACT_PROMPT = "Спасибо! Всё передал мастеру. Для связи оставьте Telegram или, если удобнее, номер телефона 😊"
SKIP_MEDIA_TEXT = "Пропустить"


def _media_keyboard(types):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(types.KeyboardButton(SKIP_MEDIA_TEXT))
    return keyboard


def start(bot, chat_id, orders_db):
    """Начать оформление индивидуального заказа."""
    order = orders_db.setdefault(chat_id, {})
    order.clear()
    order["individual_order"] = True
    order["waiting_individual_description"] = True
    order["individual_media"] = []
    bot.send_message(chat_id, INDIVIDUAL_ORDER_PROMPT)


def handle_description(bot, chat_id, text, orders_db):
    order = orders_db.setdefault(chat_id, {})
    order["individual_description"] = text
    order["waiting_individual_description"] = False
    order["waiting_individual_media_choice"] = True
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(types.KeyboardButton("Да"), types.KeyboardButton("Нет"))
    bot.send_message(chat_id, MEDIA_PROMPT, reply_markup=keyboard)


def handle_media_choice(bot, chat_id, choice, orders_db):
    order = orders_db.get(chat_id)
    if not order or not order.get("waiting_individual_media_choice"):
        return False
    if choice == "Да":
        order["waiting_individual_media_choice"] = False
        order["waiting_individual_media"] = True
        bot.send_message(chat_id, "Пришлите картинки, наброски или референсы. Можно отправить несколько файлов. Когда закончите — нажмите «Пропустить».", reply_markup=_media_keyboard(types))
        return True
    if choice == "Нет":
        order["waiting_individual_media_choice"] = False
        start_contact(bot, chat_id, orders_db)
        return True
    return False


def handle_photo(bot, chat_id, message, orders_db):
    order = orders_db.get(message.chat.id)
    if not order or not order.get("waiting_individual_media"):
        return False
    order.setdefault("individual_media", []).append({"type": "photo", "file_id": message.photo[-1].file_id})
    return True


def handle_document(bot, chat_id, message, orders_db):
    order = orders_db.get(message.chat.id)
    if not order or not order.get("waiting_individual_media"):
        return False
    order.setdefault("individual_media", []).append({"type": "document", "file_id": message.document.file_id})
    return True


def skip_media(bot, chat_id, orders_db):
    order = orders_db.get(chat_id)
    if not order or not order.get("waiting_individual_media"):
        return False
    order["waiting_individual_media"] = False
    start_contact(bot, chat_id, orders_db)
    return True


def start_contact(bot, chat_id, orders_db):
    order = orders_db.setdefault(chat_id, {})
    order["waiting_contact"] = True
    order["individual_contact"] = True
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    keyboard.row(types.KeyboardButton("💬 Не отправлять номер, связаться в ТГ"))
    bot.send_message(chat_id, CONTACT_PROMPT, reply_markup=keyboard)


def _finish(bot, chat_id, orders_db, owner_id, phone=None):
    order = orders_db.get(chat_id)
    if not order:
        return
    order["phone"] = phone
    order["waiting_contact"] = False
    order["individual_contact"] = False
    description = order.get("individual_description", "")
    username = order.get("username")
    if not username:
        username = None
    owner_text = "🧵 НОВЫЙ ИНДИВИДУАЛЬНЫЙ ЗАКАЗ\n\n"
    owner_text += f"📝 Описание:\n{description}\n\n"
    owner_text += f"👤 Клиент: {order.get('first_name') or ''}\n"
    owner_text += f"💬 Telegram: @{username}\n" if username else "💬 Telegram: не указан\n"
    owner_text += f"📱 Телефон: {phone}\n" if phone else "📱 Телефон: не предоставлен\n"
    media = order.get("individual_media", [])
    owner_text += f"\n📎 Референсов: {len(media)}"
    bot.send_message(owner_id, owner_text)
    for item in media:
        try:
            if item["type"] == "photo":
                bot.send_photo(owner_id, item["file_id"])
            else:
                bot.send_document(owner_id, item["file_id"])
        except Exception as error:
            print("Не удалось передать референс:", error)
    bot.send_message(chat_id, "Спасибо! Всё передал мастеру. Мы свяжемся с вами в рабочее время Пн–Пт, 10:00–18:00 (Екатеринбург). 😊", reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(chat_id, "Выберите, что хотите сделать.", reply_markup=_shop_keyboard(types))
    order["completed"] = True


def handle_contact(bot, chat_id, message, orders_db, owner_id):
    order = orders_db.get(chat_id)
    if not order or not order.get("individual_order") or not order.get("waiting_contact"):
        return False
    order["first_name"] = message.from_user.first_name
    order["username"] = message.from_user.username
    _finish(bot, chat_id, orders_db, owner_id, message.contact.phone_number)
    return True


def handle_no_phone(bot, chat_id, message, orders_db, owner_id):
    order = orders_db.get(chat_id)
    if not order or not order.get("individual_order") or not order.get("waiting_contact"):
        return False
    order["first_name"] = message.from_user.first_name
    order["username"] = message.from_user.username
    _finish(bot, chat_id, orders_db, owner_id, None)
    return True


def _shop_keyboard(types):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(types.KeyboardButton("🛍 Магазин"), types.KeyboardButton("📅 Записаться"))
    keyboard.row(types.KeyboardButton("🧵 Индивидуальный заказ"))
    keyboard.row(types.KeyboardButton("💬 Обратная связь"))
    return keyboard
