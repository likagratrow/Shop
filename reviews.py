"""Логика кнопки «💬 Обратная связь»."""

FEEDBACK_PROMPT = "Чем бы вы хотели поделиться?"


def start(bot, chat_id, orders_db):
    """Начать сбор обратной связи."""
    order = orders_db.setdefault(chat_id, {})
    order["feedback"] = True
    order["waiting_feedback"] = True
    bot.send_message(chat_id, FEEDBACK_PROMPT)
