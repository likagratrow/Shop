from pathlib import Path
import py_compile
import re
import subprocess


def rx(path, pattern, replacement, flags=re.S):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, replacement, text, flags=flags)
    if count != 1:
        raise SystemExit(f"{path}: expected 1 match, got {count}: {pattern[:120]!r}")
    p.write_text(new_text, encoding="utf-8")


def once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{path}: expected text not found: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# ------------------------------------------------------------
# Bot.py: remove legacy bot-side checkout/delivery flow.
# ------------------------------------------------------------
bot = Path("Bot.py")
text = bot.read_text(encoding="utf-8")
text = text.replace("import re\n", "", 1)
text = re.sub(r"^DELIVERY_SHEET_URL = .*\n", "", text, count=1, flags=re.M)
text = re.sub(r"\n\ndef load_delivery_options\(\):.*?\n\ndef format_price", "\n\ndef format_price", text, count=1, flags=re.S)
text = re.sub(r"\n\ndef format_order_items\(items_text, products\):.*?\n\ndef remove_inline_buttons", "\n\ndef remove_inline_buttons", text, count=1, flags=re.S)
text = re.sub(r"\n\ndef get_delivery_address_prompt\(delivery_id\):.*?\n\ndef send_payment_message", "\n\ndef send_payment_message", text, count=1, flags=re.S)
text = re.sub(r"\n\ndef send_payment_message\(chat_id\):.*?\n\ndef start_delivery", "\n", text, count=1, flags=re.S)
text = re.sub(r"\n\ndef start_delivery\(chat_id(?:, reason=None)?\):.*?\n\ndef after_delivery_step", "\n", text, count=1, flags=re.S)
text = re.sub(r"\n\ndef after_delivery_step\(chat_id\):.*?\n\n@bot\.message_handler\(commands=\[\"start\"\]\)", "\n\n@bot.message_handler(commands=[\"start\"])", text, count=1, flags=re.S)
text = re.sub(r"\n@bot\.message_handler\(content_types=\[\"web_app_data\"\]\)\ndef web_app_data\(message\):.*?\n\n@bot\.callback_query_handler\(func=lambda call: call\.data == \"paid\"\)", "\n@bot.callback_query_handler(func=lambda call: call.data == \"paid\")", text, count=1, flags=re.S)

contact_block = '''@bot.message_handler(content_types=["contact"])
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
text = re.sub(r"@bot\.message_handler\(content_types=\[\"contact\"\]\).*?\nprint\(\"Бот запущен\"\)", contact_block + "\n\nprint(\"Бот запущен\")", text, count=1, flags=re.S)
bot.write_text(text, encoding="utf-8")

# Owner: include foreign country when present.
once("Bot.py", "    delivery_service = order.get(\"delivery_service\")\n    delivery_address = order.get(\"delivery_address\")\n", "    delivery_service = order.get(\"delivery_service\")\n    delivery_country = order.get(\"delivery_country\")\n    delivery_address = order.get(\"delivery_address\")\n")
once("Bot.py", "    if delivery_service: owner_text += f\"📦 Служба доставки: {delivery_service}\\n\"\n    if delivery_address: owner_text += f\"📍 Куда доставить: {delivery_address}\\n\"\n", "    if delivery_service: owner_text += f\"📦 Служба доставки: {delivery_service}\\n\"\n    if delivery_country: owner_text += f\"🌍 Страна: {delivery_country}\\n\"\n    if delivery_address: owner_text += f\"📍 Куда доставить: {delivery_address}\\n\"\n")

# ------------------------------------------------------------
# Orders: syntax-safe Telegram message strings.
# ------------------------------------------------------------
send_message = '''function sendOrderMessage(chatId, orderId, itemsText, products, totals) {
  const botToken = getBotToken();
  const delivery = totals.delivery || {};
  let text = `Ваш заказ №${orderId}:\\n\\n${itemsText}\\n\\n`;

  if (delivery.method_id) {
    text += `🚚 Доставка: ${delivery.method_title}`;
    text += delivery.price !== null && delivery.price !== undefined
      ? ` — ${formatMoney(delivery.price)} ₽`
      : ' — договорная';
    text += '\\n';
    if (delivery.service_title) text += `📦 Служба доставки: ${delivery.service_title}\\n`;
    if (delivery.country) text += `🌍 Страна: ${delivery.country}\\n`;
    if (delivery.address) text += `📍 Адрес: ${delivery.address}\\n`;
    text += '\\n';
  }

  if (totals.repeatOrder) {
    text += '⚒️ Заказ на изготовление/сервис.\\n\\nОставьте контакт, и мастер свяжется с вами по поводу заказа.';
    telegramApi(botToken, 'sendMessage', {
      chat_id: chatId,
      text: text,
      reply_markup: JSON.stringify({inline_keyboard: [[{text: '📞 Оставить контакт', callback_data: 'order_contact'}]]})
    });
    return;
  }

  text += `💰 Товары к оплате: <b>${formatMoney(totals.payableGoodsTotal)} ₽</b>\\n`;
  if (totals.mixedOrder && totals.repeatTotal > 0) {
    text += `⚒️ На заказ: ${formatMoney(totals.repeatTotal)} ₽\\n`;
  }
  if (delivery.price === null && delivery.method_id) {
    text += `💰 Итого: <b>${formatMoney(totals.payableTotal)} ₽</b> + доставка по согласованию\\n\\n`;
  } else {
    text += `💰 Итого: <b>${formatMoney(totals.total)} ₽</b>\\n\\n`;
  }
  text += '💳 Оплата переводом на Сбербанк:\\n' +
    '📱 +79089147913\\n' +
    '👤 Получатель: Лия П.\\n\\n' +
    '📦 Заказ будет собран после оплаты.\\n\\n' +
    'Вы можете перевести оплату сейчас или дождаться связи с менеджером в рабочее время:\\n' +
    'Пн–Пт, 10:00–18:00 (Екатеринбург).';

  telegramApi(botToken, 'sendMessage', {
    chat_id: chatId,
    text: text,
    parse_mode: 'HTML',
    reply_markup: JSON.stringify({inline_keyboard: [[
      {text: '💳 Я оплатил', callback_data: 'paid'},
      {text: '⏳ Подожду менеджера', callback_data: 'wait_manager'}
    ]]})
  });
}
'''
rx("Orders", r"function sendOrderMessage\(chatId, orderId, itemsText, products, totals\) \{.*?\n\}\n\nfunction getOrderForBot", send_message + "\nfunction getOrderForBot")

# ------------------------------------------------------------
# app.js: cards and modal show only a button; quantity stays in cart.
# ------------------------------------------------------------
rx("app.js", r"function getCardButtonHtml\(product\) \{.*?\n\}\n\nfunction updateProductCard", '''function getCardButtonHtml(product) {
    if (product.balance <= 0) return `<button type="button" class="card-cart-btn" disabled>Нет в наличии</button>`;
    const quantity = getCartQuantity(product.id);
    return `<button type="button" class="card-cart-btn" onclick="event.stopPropagation(); addToCart(${JSON.stringify(product.id)});">${quantity > 0 ? 'В корзине' : 'В корзину'}</button>`;
}

function updateProductCard''')
rx("app.js", r"    const currentQuantity = getCartQuantity\(product\.id\);\n    const displayedQuantity = .*?\n    const quantityHtml = product\.category === 'items' \? .*? : '';", "    const currentQuantity = getCartQuantity(product.id);\n    const quantityHtml = '';")
rx("app.js", r"\$\{product\.balance <= 0 \? 'Нет в наличии' : currentQuantity > 0 \? 'Добавить ещё' : 'В корзину'\}", "${product.balance <= 0 ? 'Нет в наличии' : 'В корзину'}", flags=0)

# Syntax validation.
py_compile.compile("Bot.py", doraise=True)
py_compile.compile("commands.py", doraise=True)
py_compile.compile("orders_bridge.py", doraise=True)
subprocess.run(["node", "--check", "Orders"], check=True)
subprocess.run(["node", "--check", "app.js"], check=True)
subprocess.run(["node", "--check", "delivery.js"], check=True)
print("Shop v5 syntax checks passed")
