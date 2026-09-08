"""Логика кнопки «💬 Обратная связь»."""

from telebot import types

FEEDBACK_PROMPT = "Чем бы вы хотели поделиться?"
CONTACT_QUESTION = "Хотите, чтобы мы связались с вами по этому поводу?"
YES_TEXT = "💬 Да, связаться в ТГ"
NO_TEXT = "Нет"


def _choice_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(types.KeyboardButton(YES_TEXT), types.KeyboardButton(NO_TEXT))
    return keyboard


def _shop_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(types.KeyboardButton("🛍 Магазин", web_app=types.WebAppInfo(url="https://likagratrow.github.io/Shop/")), types.KeyboardButton("📅 Записаться"))
    keyboard.row(types.KeyboardButton("🧵 Индивидуальный заказ"))
    keyboard.row(types.KeyboardButton("💬 Обратная связь"))
    return keyboard


def handle_feedback(bot, chat_id, text, orders_db):
    order = orders_db.get(chat_id)
    if not order or not order.get("waiting_feedback"):
        return False
    order["feedback_text"] = text
    order["waiting_feedback"] = False
    order["waiting_feedback_contact_choice"] = True
    bot.send_message(chat_id, CONTACT_QUESTION, reply_markup=_choice_keyboard())
    return True


def handle_contact_choice(bot, chat_id, choice, orders_db, first_name, username):
    order = orders_db.get(chat_id)
    if not order or not order.get("waiting_feedback_contact_choice"):
        return False
    if choice not in (YES_TEXT, NO_TEXT):
        return False
    from Bot import YOUR_TELEGRAM_ID
    wants_contact = choice == YES_TEXT
    order["waiting_feedback_contact_choice"] = False
    order["feedback_wants_contact"] = wants_contact
    order["first_name"] = first_name
    order["username"] = username
    owner_text = "💬 НОВАЯ ОБРАТНАЯ СВЯЗЬ\n\n"
    owner_text += f"{order.get('feedback_text', '')}\n\n"
    owner_text += f"👤 Клиент: {first_name or ''}\n"
    owner_text += f"💬 Telegram: @{username}\n" if username else "💬 Telegram: не указан\n"
    owner_text += f"📲 Связаться обратно: {'да' if wants_contact else 'нет'}"
    bot.send_message(YOUR_TELEGRAM_ID, owner_text)
    bot.send_message(chat_id, "Спасибо! Ваше сообщение передано.", reply_markup=_shop_keyboard())
    order["completed"] = True
    return True


def _is_relevant(message, orders_db):
    order = orders_db.get(message.chat.id)
    return bool(order and order.get("feedback") and not order.get("completed") and message.content_type == "text" and (order.get("waiting_feedback") or order.get("waiting_feedback_contact_choice")))


def _dispatch(bot, message, orders_db):
    order = orders_db.get(message.chat.id)
    if order.get("waiting_feedback"):
        return handle_feedback(bot, message.chat.id, message.text, orders_db)
    if order.get("waiting_feedback_contact_choice"):
        return handle_contact_choice(bot, message.chat.id, message.text, orders_db, message.from_user.first_name, message.from_user.username)
    return False


def _register_dispatcher(bot, orders_db):
    if getattr(bot, "_reviews_dispatcher", False):
        return
    def dispatcher(message):
        return _dispatch(bot, message, orders_db)
    bot.register_message_handler(dispatcher, content_types=["text"], func=lambda message: _is_relevant(message, orders_db))
    bot.message_handlers.insert(0, bot.message_handlers.pop())
    bot._reviews_dispatcher = True


def start(bot, chat_id, orders_db):
    _register_dispatcher(bot, orders_db)
    order = orders_db.setdefault(chat_id, {})
    order.clear()
    order["feedback"] = True
    order["waiting_feedback"] = True
    bot.send_message(chat_id, FEEDBACK_PROMPT)
