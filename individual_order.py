"""Логика кнопки «🧵 Индивидуальный заказ»."""

INDIVIDUAL_ORDER_PROMPT = "Опишите, что бы вы хотели заказать?"


def start(bot, chat_id, orders_db):
    """Начать оформление индивидуального заказа."""
    order = orders_db.setdefault(chat_id, {})
    order["individual_order"] = True
    order["waiting_individual_description"] = True
    bot.send_message(chat_id, INDIVIDUAL_ORDER_PROMPT)
