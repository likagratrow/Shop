// ==================================================
// ДОСТАВКА В ЗАКАЗЕ
// ==================================================
// Этот файл только добавляет в payload заказа признак,
// нужна ли доставка, и данные каждого товара.

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
        cart.some(item => {
            const category = String(item.category || '').trim().toLowerCase();
            return category === 'items' || category === 'repeat';
        });

    const payload =
        JSON.stringify({
            items: itemsText,
            products: cart.map(item => ({
                id: item.id,
                quantity: item.count,
                category: item.category,
                price: item.price
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