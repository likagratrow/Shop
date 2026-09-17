import json
import sys
import urllib.request

from config import BOT_TOKEN


ORDERS_API_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbz2XQn7s0e_irZ2rRsvcXb_I7hKp_DxNXTYsZlIt2TATE58IiqJ9AyjUKj9f09-CII9/exec"
)


def _main():
    return sys.modules["__main__"]


def _bot():
    return _main().bot


def _orders_db():
    return _main().orders_db


def _load_order(chat_id, order_id):
    payload = json.dumps(
        {
            "action": "get-order",
            "order_id": str(order_id),
            "telegram_id": str(chat_id),
            "api_token": BOT_TOKEN,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        ORDERS_API_URL,
        data=payload,
        headers={
            "Content-Type": "text/plain;charset=utf-8",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        print("Ошибка получения заказа из Orders:", repr(error))
        return None, "Не удалось получить данные заказа."

    if not result.get("ok"):
        return None, result.get("error", "Не удалось получить данные заказа.")

    source = result.get("order") or {}
    username = str(source.get("username") or "").lstrip("@")

    order = {
        "items": source.get("items", ""),
        "products": source.get("products", []),
        "product_total": source.get("product_total", 0),
        "payable_goods_total": source.get("payable_goods_total", 0),
        "payable_total": source.get("payable_total", 0),
        "managed_product_total": source.get("managed_product_total", 0),
        "total": source.get("total", 0),
        "needs_delivery": bool(source.get("needs_delivery", False)),
        "managed_order": bool(source.get("managed_order", False)),
        "repeat_order": bool(source.get("repeat_order", False)),
        "service_order": bool(source.get("service_order", False)),
        "mixed_order": bool(source.get("mixed_order", False)),
        "delivery_id": str(source.get("delivery_id") or source.get("receiving") or "").strip(),
        "delivery_title": str(source.get("delivery_title") or "").strip(),
        "delivery_price": source.get("delivery_price"),
        "delivery_service": str(source.get("delivery_service") or "").strip(),
        "delivery_country": str(source.get("delivery_country") or "").strip(),
        "delivery_address": str(source.get("delivery_address") or source.get("address") or "").strip(),
        "username": username,
        "first_name": "",
        "completed": False,
    }

    _orders_db()[chat_id] = order
    return order, None


def _load_and_call(call, callback_name, order_id):
    chat_id = call.message.chat.id
    order, error = _load_order(chat_id, order_id)

    if not order:
        try:
            _bot().answer_callback_query(call.id, error or "Заказ не найден.")
        except Exception:
            pass
        return

    order["first_name"] = call.from_user.first_name or ""
    if call.from_user.username:
        order["username"] = call.from_user.username

    handler = getattr(_main(), callback_name, None)
    if handler is None:
        try:
            _bot().answer_callback_query(call.id, "Не найден обработчик заказа.")
        except Exception:
            pass
        return

    handler(call)


def register():
    bot = _bot()

    @bot.callback_query_handler(
        func=lambda call: call.data == "paid" and "Ваш заказ №" in str(call.message.text or "")
    )
    def paid_from_orders(call):
        order_id = _latest_order_id_from_callback_message(call)
        if order_id:
            _load_and_call(call, "paid", order_id)
        else:
            try:
                bot.answer_callback_query(call.id, "Не удалось определить заказ.")
            except Exception:
                pass

    @bot.callback_query_handler(
        func=lambda call: call.data == "wait_manager" and "Ваш заказ №" in str(call.message.text or "")
    )
    def wait_manager_from_orders(call):
        order_id = _latest_order_id_from_callback_message(call)
        if order_id:
            _load_and_call(call, "wait_manager", order_id)
        else:
            try:
                bot.answer_callback_query(call.id, "Не удалось определить заказ.")
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: str(call.data).startswith("order_contact"))
    def managed_contact_from_orders(call):
        order_id = _latest_order_id_from_callback_message(call)

        if not order_id:
            try:
                bot.answer_callback_query(call.id, "Не удалось определить заказ.")
            except Exception:
                pass
            return

        order, error = _load_order(call.message.chat.id, order_id)
        if not order:
            try:
                bot.answer_callback_query(call.id, error or "Заказ не найден.")
            except Exception:
                pass
            return

        order["first_name"] = call.from_user.first_name or ""
        if call.from_user.username:
            order["username"] = call.from_user.username

        try:
            bot.answer_callback_query(call.id, "Хорошо")
        except Exception:
            pass

        request_contact = getattr(_main(), "request_contact", None)
        managed_contact_text = getattr(_main(), "MANAGED_CONTACT_TEXT", "Оставьте контакт, и менеджер свяжется с вами.")
        if request_contact:
            request_contact(call.message.chat.id, managed_contact_text)


def _latest_order_id_from_callback_message(call):
    text = str(call.message.text or "")
    marker = "Ваш заказ №"

    if marker not in text:
        return ""

    tail = text.split(marker, 1)[1]
    digits = ""

    for char in tail:
        if char.isdigit():
            digits += char
        else:
            break

    return digits
