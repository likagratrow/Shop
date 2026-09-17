from pathlib import Path
import py_compile
import re

p = Path('Bot.py')
text = p.read_text(encoding='utf-8')

text = text.replace('import re\n', '', 1)
text = re.sub(r'^DELIVERY_SHEET_URL = .*\n', '', text, count=1, flags=re.M)
text = re.sub(r'\n\ndef load_delivery_options\(\):.*?\n\ndef delivery_keyboard', '\n\ndef delivery_keyboard', text, count=1, flags=re.S)
text = re.sub(r'\n\ndef delivery_keyboard\(options\):.*?\n\ndef format_price', '\n\ndef format_price', text, count=1, flags=re.S)
text = re.sub(r'\n\ndef format_order_items\(items_text, products\):.*?\n\ndef remove_inline_buttons', '\n\ndef remove_inline_buttons', text, count=1, flags=re.S)
text = re.sub(r'\n\ndef get_delivery_address_prompt\(delivery_id\):.*?\n\ndef send_payment_message', '\n\ndef send_payment_message', text, count=1, flags=re.S)
text = re.sub(r'\n\ndef send_payment_message\(chat_id\):.*?\n\ndef start_delivery', '\n\ndef start_delivery', text, count=1, flags=re.S)
text = re.sub(r'\n\ndef start_delivery\(chat_id, reason=None\):.*?\n\ndef after_delivery_step', '\n\ndef after_delivery_step', text, count=1, flags=re.S)
text = re.sub(r'\n\ndef after_delivery_step\(chat_id\):.*?\n\n@bot\.message_handler\(commands=\["start"\]\)', '\n\n@bot.message_handler(commands=["start"])', text, count=1, flags=re.S)
text = re.sub(r'\n@bot\.message_handler\(content_types=\["web_app_data"\]\)\ndef web_app_data\(message\):.*?\n\n@bot\.callback_query_handler\(func=lambda call: call\.data == "paid"\)', '\n@bot.callback_query_handler(func=lambda call: call.data == "paid")', text, count=1, flags=re.S)

new_contacts = '''@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    chat_id = message.chat.id
    order = orders_db.get(chat_id)
    if not order or not order.get("waiting_contact"):
        return
    order["phone"] = message.contact.phone_number
    order["waiting_contact"] = False
    if order.get("contact_reason"):
        send_owner_notification(chat_id)
        bot.send_message(chat_id, "Спасибо! Я передал информацию менеджеру, мы свяжемся с вами для уточнения деталей.", reply_markup=shop_keyboard())
        return
    if order.get("repeat_order"):
        finish_repeat_order(chat_id)
        return
    if order.get("mixed_order"):
        send_owner_notification(chat_id)
        if order.get("paid_status"):
            send_final_order_message(chat_id)
        elif order.get("waiting_manager"):
            bot.send_message(chat_id, "Хорошо 😊\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.", reply_markup=shop_keyboard())
        return
    if order.get("paid_status"):
        send_owner_notification(chat_id)
        send_final_order_message(chat_id)
    elif order.get("waiting_manager"):
        send_owner_notification(chat_id)
        bot.send_message(chat_id, "Хорошо 😊\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.", reply_markup=shop_keyboard())


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
        bot.send_message(chat_id, "Спасибо! Я передал информацию менеджеру, мы свяжемся с вами для уточнения деталей.", reply_markup=shop_keyboard())
        return
    if order.get("repeat_order"):
        finish_repeat_order(chat_id)
        return
    if order.get("mixed_order"):
        send_owner_notification(chat_id)
        if order.get("paid_status"):
            send_final_order_message(chat_id)
        elif order.get("waiting_manager"):
            bot.send_message(chat_id, "Хорошо 😊\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.", reply_markup=shop_keyboard())
        return
    if order.get("paid_status"):
        send_owner_notification(chat_id)
        send_final_order_message(chat_id)
    elif order.get("waiting_manager"):
        send_owner_notification(chat_id)
        bot.send_message(chat_id, "Хорошо 😊\nМенеджер свяжется с вами в рабочее время Пн-Пт 10-18.", reply_markup=shop_keyboard())


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
            bot.send_message(YOUR_TELEGRAM_ID, f"💬 НОВАЯ ОБРАТНАЯ СВЯЗЬ\n\n{message.text}\n\n👤 Клиент: {message.from_user.first_name or ''}\n💬 Telegram: @{message.from_user.username}")
        else:
            bot.send_message(YOUR_TELEGRAM_ID, f"💬 НОВАЯ ОБРАТНАЯ СВЯЗЬ\n\n{message.text}\n\n👤 Клиент: {message.from_user.first_name or ''}")
        bot.send_message(chat_id, "Спасибо! Ваше сообщение передано.", reply_markup=shop_keyboard())
        return
'''
text, count = re.subn(r'@bot\.message_handler\(content_types=\["contact"\]\).*?\nprint\("Бот запущен"\)', new_contacts + '\n\nprint("Бот запущен")', text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f'contacts block mismatch: {count}')

old = '    delivery_service = order.get("delivery_service")\n    delivery_address = order.get("delivery_address")\n'
new = '    delivery_service = order.get("delivery_service")\n    delivery_country = order.get("delivery_country")\n    delivery_address = order.get("delivery_address")\n'
if old not in text:
    raise SystemExit('owner delivery variables not found')
text = text.replace(old, new, 1)

old = '    if delivery_service: owner_text += f"📦 Служба доставки: {delivery_service}\\n"\n    if delivery_address: owner_text += f"📍 Куда доставить: {delivery_address}\\n"\n'
new = '    if delivery_service: owner_text += f"📦 Служба доставки: {delivery_service}\\n"\n    if delivery_country: owner_text += f"🌍 Страна: {delivery_country}\\n"\n    if delivery_address: owner_text += f"📍 Куда доставить: {delivery_address}\\n"\n'
if old not in text:
    raise SystemExit('owner delivery lines not found')
text = text.replace(old, new, 1)

p.write_text(text, encoding='utf-8')
py_compile.compile('Bot.py', doraise=True)
print('Bot.py OK')
