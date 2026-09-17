// ==================================================
// ОТПРАВКА ЗАКАЗА В ORDERS
// ==================================================

const ORDERS_API_URL =
    'https://script.google.com/macros/s/AKfycbz2XQn7s0e_irZ2rRsvcXb_I7hKp_DxNXTYsZlIt2TATE58IiqJ9AyjUKj9f09-CII9/exec';


sendOrder = async function() {

    if (!cart.length) return;

    if (!tg?.initData) {
        alert('Заказ можно оформить только внутри Telegram.');
        return;
    }

    const total =
        cart.reduce(
            (sum, item) =>
                sum +
                Number(item.price || 0) *
                Number(item.count || 0),
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

    const payload = {
        action: 'create-order',
        initData: tg.initData,
        items: itemsText,
        products: cart.map(item => ({
            id: item.id,
            name: item.name,
            quantity: item.count,
            category: item.category,
            price: Number(item.price || 0)
        })),
        total: total,
        needs_delivery: needsDelivery
    };

    try {
        const response = await fetch(
            ORDERS_API_URL,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'text/plain;charset=utf-8'
                },
                body: JSON.stringify(payload),
                cache: 'no-store'
            }
        );

        if (!response.ok) {
            throw new Error(`Orders вернул HTTP ${response.status}`);
        }

        const result = await response.json();

        if (!result?.ok) {
            throw new Error(result?.error || 'Не удалось создать заказ.');
        }

        tg.close();

    } catch (error) {
        console.error('Ошибка отправки заказа:', error);
        alert(
            'Не удалось оформить заказ.\n\n' +
            (error?.message || 'Попробуйте ещё раз.')
        );
    }
};
