// ==================================================
// ДОСТАВКА В ЗАКАЗЕ
// ==================================================
// Этот файл только добавляет в payload заказа признак,
// нужна ли доставка, и категорию каждого товара.

sendOrder = function() {

    if (!cart.length) return;

    const total =
        cart.reduce(
            (sum, item) =>
                sum +
                item.price *
                item.count,
            0
        );

    const itemsText =
        cart
            .map(
                item =>
                    `${item.name} (x${item.count})`
            )
            .join(', ');

    const needsDelivery =
        cart.some(
            item =>
                String(item.category || '').trim().toLowerCase() === 'items'
        );

    const payload =
        JSON.stringify({
            items: itemsText,
            products: cart.map(item => ({
                id: item.id,
                quantity: item.count,
                category: item.category
            })),
            total: total,
            needs_delivery: needsDelivery
        });

    if (tg?.sendData) {
        tg.sendData(payload);
        tg.close();
    } else {
        alert(
            'Заказ можно оформить только внутри Telegram.'
        );
    }
};