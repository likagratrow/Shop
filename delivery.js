// ==================================================
// SHOP CHECKOUT: ДОСТАВКА + СЕРВИС + ОСТАТКИ
// ==================================================

const DELIVERY_SHEET_URL_V3 =
    `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=${encodeURIComponent('Доставка')}`;

let currentSubcategory = 'all';
let deliveryCatalog = null;
let checkoutState = null;

const previousRenderV3 = render;
const previousFilterCategoryV3 = filterCategory;
const previousLoadProductsV3 = loadProducts;
const previousGetCardButtonHtmlV3 = getCardButtonHtml;

// --------------------------------------------------
// Остатки в карточке: никогда не показываем число.
// --------------------------------------------------

getStockText = function(product) {
    return product && (product.balance === Infinity || product.balance > 0)
        ? 'В наличии'
        : 'Нет в наличии';
};

getCardButtonHtml = function(product) {
    if (!product || product.balance <= 0) {
        return '<button type="button" class="card-cart-btn" disabled>Нет в наличии</button>';
    }

    const quantity = getCartQuantity(product.id);
    return `<button type="button" class="card-cart-btn" onclick="event.stopPropagation(); addToCart(${JSON.stringify(product.id)});">${quantity > 0 ? 'В корзине' : 'В корзину'}</button>`;
};

// --------------------------------------------------
// Подкатегории сервиса: колонка O = Подкатегория.
// --------------------------------------------------

async function loadServiceSubcategoriesV3() {
    try {
        const response = await fetch(SHEET_URL, {method: 'GET', cache: 'no-store'});
        if (!response.ok) return;

        const text = await response.text();
        const json = parseGvizResponse(text);
        const rows = json?.table?.rows;
        if (!Array.isArray(rows)) return;

        products.forEach((product, index) => {
            const cells = rows[index]?.c || [];
            product.subcategory = String(cells[14]?.v ?? '').trim();
            product.subcategoryKey = product.subcategory.toLowerCase();
        });
    } catch (error) {
        console.warn('Не удалось загрузить подкатегории сервиса:', error);
    }
}

function renderServiceSubcategoriesV3() {
    const container = document.getElementById('service-subcategories');
    if (!container) return;

    if (currentCategory !== 'service') {
        container.hidden = true;
        container.innerHTML = '';
        return;
    }

    const values = [];
    const seen = new Set();

    products
        .filter(product => product.category === 'service')
        .forEach(product => {
            const label = String(product.subcategory || '').trim();
            const key = label.toLowerCase();
            if (!key || seen.has(key)) return;
            seen.add(key);
            values.push({key, label});
        });

    values.sort((a, b) => a.label.localeCompare(b.label, 'ru', {sensitivity: 'base'}));

    const buttons = [
        `<button type="button" class="service-subcat-btn ${currentSubcategory === 'all' ? 'active' : ''}" data-subcategory="all">Все</button>`,
        ...values.map(item => `<button type="button" class="service-subcat-btn ${currentSubcategory === item.key ? 'active' : ''}" data-subcategory="${escapeHtml(item.key)}">${escapeHtml(item.label)}</button>`)
    ];

    container.innerHTML = buttons.join('');
    container.hidden = false;

    container.querySelectorAll('.service-subcat-btn').forEach(button => {
        button.addEventListener('click', () => {
            currentSubcategory = button.dataset.subcategory || 'all';
            container.querySelectorAll('.service-subcat-btn').forEach(item => item.classList.remove('active'));
            button.classList.add('active');
            render();
        });
    });
}

render = function() {
    const fullProducts = products;
    const shouldFilterService = currentCategory === 'service' && currentSubcategory !== 'all';

    if (shouldFilterService) {
        products = fullProducts.filter(product => product.subcategoryKey === currentSubcategory);
    }

    try {
        previousRenderV3();
    } finally {
        products = fullProducts;
    }

    renderServiceSubcategoriesV3();
};

filterCategory = function(category, button) {
    currentSubcategory = 'all';
    previousFilterCategoryV3(category, button);
    renderServiceSubcategoriesV3();
};

loadProducts = async function() {
    await previousLoadProductsV3();
    await loadServiceSubcategoriesV3();
    render();
};

// --------------------------------------------------
// Стили нового checkout и подкатегорий.
// --------------------------------------------------

const checkoutStyleV3 = document.createElement('style');
checkoutStyleV3.textContent = `
    .service-subcategories {
        display: flex;
        gap: 6px;
        overflow-x: auto;
        padding: 0 0 10px;
        margin-bottom: 5px;
        scrollbar-width: none;
    }
    .service-subcategories::-webkit-scrollbar { display: none; }
    .service-subcat-btn {
        flex: 0 0 auto;
        border: none;
        border-radius: 18px;
        padding: 7px 11px;
        background: var(--tg-theme-secondary-bg-color, #eee);
        color: var(--tg-theme-text-color, #000);
        white-space: nowrap;
    }
    .service-subcat-btn.active {
        background: var(--tg-theme-button-color, #2481cc);
        color: var(--tg-theme-button-text-color, #fff);
    }
    .cart-checkout { margin: 12px 0; }
    .checkout-title { font-weight: 700; margin-bottom: 10px; }
    .checkout-summary { margin-bottom: 12px; font-size: 14px; line-height: 1.45; }
    .checkout-option {
        width: 100%;
        margin: 5px 0;
        padding: 11px 12px;
        border: 1px solid color-mix(in srgb, var(--tg-theme-button-color, #2481cc) 22%, transparent);
        border-radius: 10px;
        background: var(--tg-theme-secondary-bg-color, #f5f5f5);
        color: var(--tg-theme-text-color, #000);
        text-align: left;
    }
    .checkout-option small { opacity: .75; }
    .checkout-input,
    .checkout-country-search {
        width: 100%;
        box-sizing: border-box;
        padding: 11px 12px;
        margin: 6px 0 10px;
        border-radius: 9px;
        border: 1px solid #ccc;
        background: var(--tg-theme-secondary-bg-color, #eee);
        color: currentcolor;
    }
    .checkout-country-list {
        max-height: 260px;
        overflow-y: auto;
        margin: 4px 0 10px;
        border: 1px solid #ddd;
        border-radius: 9px;
    }
    .checkout-country-item {
        width: 100%;
        padding: 10px 12px;
        border: none;
        border-bottom: 1px solid #eee;
        background: transparent;
        color: currentcolor;
        text-align: left;
    }
    .checkout-country-item:last-child { border-bottom: 0; }
    .checkout-actions { display: flex; gap: 8px; margin-top: 10px; }
    .checkout-actions button { flex: 1; }
    .checkout-back { background: var(--tg-theme-secondary-bg-color, #eee) !important; color: var(--tg-theme-text-color, #000) !important; }
    .checkout-error { color: #b00020; margin: 7px 0; font-size: 14px; }
`;
document.head.appendChild(checkoutStyleV3);

// --------------------------------------------------
// Страны — получаем через Intl.DisplayNames, без внешнего API.
// --------------------------------------------------

let countriesV3 = null;

function getCountriesV3() {
    if (countriesV3) return countriesV3;

    if (typeof Intl === 'undefined' || typeof Intl.DisplayNames !== 'function') {
        countriesV3 = [];
        return countriesV3;
    }

    const displayNames = new Intl.DisplayNames(['ru'], {type: 'region'});
    const specialCodes = new Set(['EU', 'UN', 'QO', 'ZZ']);
    const result = [];

    for (let first = 65; first <= 90; first++) {
        for (let second = 65; second <= 90; second++) {
            const code = String.fromCharCode(first, second) + String.fromCharCode(second === 64 ? 65 : 65);
        }
    }

    for (let first = 65; first <= 90; first++) {
        for (let second = 65; second <= 90; second++) {
            const code = String.fromCharCode(first) + String.fromCharCode(second);
            if (specialCodes.has(code)) continue;
            try {
                const name = String(displayNames.of(code) || '').trim();
                if (!name || name.toUpperCase() === code) continue;
                result.push(name);
            } catch (error) {
                // Недопустимые пары регионов просто пропускаем.
            }
        }
    }

    countriesV3 = [...new Set(result)].sort((a, b) => a.localeCompare(b, 'ru', {sensitivity: 'base'}));
    return countriesV3;
}

// --------------------------------------------------
// Таблица доставки.
// A ID, B Название, C Цена, D Тип, E Для.
// Старые строки без D считаются способами доставки.
// --------------------------------------------------

async function loadDeliveryCatalogV3() {
    if (deliveryCatalog) return deliveryCatalog;

    const response = await fetch(DELIVERY_SHEET_URL_V3, {method: 'GET', cache: 'no-store'});
    if (!response.ok) throw new Error(`Не удалось загрузить варианты доставки: HTTP ${response.status}`);

    const json = parseGvizResponse(await response.text());
    const rows = json?.table?.rows;
    if (!Array.isArray(rows)) throw new Error('Вкладка «Доставка» не вернула строки.');

    const methods = [];
    const services = [];

    rows.forEach(row => {
        const cells = row.c || [];
        const id = String(cells[0]?.v ?? '').trim();
        const title = String(cells[1]?.v ?? '').trim();
        const priceText = String(cells[2]?.v ?? '').trim();
        const kind = String(cells[3]?.v ?? 'method').trim().toLowerCase() || 'method';
        const scope = String(cells[4]?.v ?? '').trim().toLowerCase();
        if (!id || !title) return;

        let price = null;
        if (priceText && !/договор/i.test(priceText)) {
            const parsed = Number(priceText.replace(/\s/g, '').replace(',', '.').replace('₽', ''));
            if (Number.isFinite(parsed)) price = parsed;
        }

        const item = {id, title, price, scope};
        if (kind === 'service') services.push(item);
        else methods.push(item);
    });

    deliveryCatalog = {methods, services};
    return deliveryCatalog;
}

function formatDeliveryPriceV3(price) {
    return price == null ? 'договорная' : `${formatPrice(price)} ₽`;
}

function methodsNeedDeliveryV3() {
    return cart.some(item => {
        const category = String(item.category || '').trim().toLowerCase();
        return category === 'items' || category === 'repeat';
    });
}

function productsTotalV3() {
    return cart.reduce((sum, item) => sum + Number(item.price || 0) * Number(item.count || 0), 0);
}

function showCheckoutV3(content) {
    const block = document.getElementById('cart-checkout');
    if (!block) return;
    block.hidden = false;
    block.innerHTML = content;
}

function hideCheckoutV3() {
    const block = document.getElementById('cart-checkout');
    if (block) {
        block.hidden = true;
        block.innerHTML = '';
    }
    checkoutState = null;
}

function updateCheckoutTotalV3(deliveryPrice) {
    const productTotal = productsTotalV3();
    const total = deliveryPrice == null ? productTotal : productTotal + Number(deliveryPrice || 0);
    const totalEl = document.getElementById('cart-total');
    if (totalEl) totalEl.innerText = formatPrice(total);
}

async function openDeliveryCheckoutV3() {
    const catalog = await loadDeliveryCatalogV3();
    checkoutState = {method: null, service: null, country: '', address: '', delivery: null};

    const productTotal = productsTotalV3();
    const methodsHtml = catalog.methods.map(method => `
        <button type="button" class="checkout-option" data-delivery-method="${escapeHtml(method.id)}">
            <b>${escapeHtml(method.title)}</b><br>
            <small>${escapeHtml(formatDeliveryPriceV3(method.price))}</small>
        </button>
    `).join('');

    showCheckoutV3(`
        <div class="checkout-title">🚚 Выберите способ получения</div>
        <div class="checkout-summary">Товары: <b>${formatPrice(productTotal)} ₽</b></div>
        ${methodsHtml || '<div class="checkout-error">В таблице «Доставка» пока нет способов получения.</div>'}
    `);

    document.querySelectorAll('[data-delivery-method]').forEach(button => {
        button.addEventListener('click', async () => {
            const method = catalog.methods.find(item => item.id === button.dataset.deliveryMethod);
            if (!method) return;
            checkoutState.method = method;
            await renderDeliveryStepV3();
        });
    });
}

async function renderDeliveryStepV3() {
    const method = checkoutState.method;
    const block = document.getElementById('cart-checkout');
    if (!method || !block) return;

    checkoutState.service = null;
    checkoutState.country = '';
    checkoutState.address = '';

    if (method.id === 'pickup') {
        checkoutState.delivery = {
            method_id: method.id,
            method_title: method.title,
            price: method.price
        };
        updateCheckoutTotalV3(method.price);
        showCheckoutV3(`
            <div class="checkout-title">✓ ${escapeHtml(method.title)}</div>
            <div class="checkout-summary">Стоимость доставки: <b>${escapeHtml(formatDeliveryPriceV3(method.price))}</b></div>
            <div class="checkout-actions">
                <button type="button" class="order-btn" id="checkout-submit">Оформить заказ</button>
                <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
            </div>
        `);
        bindCheckoutSubmitV3();
        return;
    }

    if (method.id === 'courier_ekb') {
        updateCheckoutTotalV3(method.price);
        showCheckoutV3(`
            <div class="checkout-title">📍 ${escapeHtml(method.title)}</div>
            <div class="checkout-summary">Стоимость доставки: <b>${escapeHtml(formatDeliveryPriceV3(method.price))}</b></div>
            <input id="delivery-address" class="checkout-input" type="text" placeholder="Улица, дом, квартира" autocomplete="street-address">
            <div class="checkout-actions">
                <button type="button" class="order-btn" id="checkout-submit">Оформить заказ</button>
                <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
            </div>
            <div id="checkout-error" class="checkout-error"></div>
        `);
        bindAddressSubmitV3();
        return;
    }

    if (method.id === 'russia') {
        const services = deliveryCatalog.services.filter(service => {
            const scopes = service.scope.split(',').map(value => value.trim()).filter(Boolean);
            return !scopes.length || scopes.includes('russia');
        });

        updateCheckoutTotalV3(method.price);
        showCheckoutV3(`
            <div class="checkout-title">📦 Сначала выберите службу доставки</div>
            <div class="checkout-summary">Доставка по РФ: <b>${escapeHtml(formatDeliveryPriceV3(method.price))}</b></div>
            <div id="delivery-services">
                ${services.map(service => `
                    <button type="button" class="checkout-option" data-delivery-service="${escapeHtml(service.id)}">${escapeHtml(service.title)}</button>
                `).join('') || '<div class="checkout-error">Добавьте службы доставки на вкладку «Доставка».</div>'}
            </div>
            <div id="delivery-point-form"></div>
            <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
        `);

        document.querySelectorAll('[data-delivery-service]').forEach(button => {
            button.addEventListener('click', () => {
                checkoutState.service = services.find(item => item.id === button.dataset.deliveryService) || null;
                renderRussiaPointV3();
            });
        });
        return;
    }

    if (method.id === 'abroad') {
        updateCheckoutTotalV3(null);
        renderAbroadCountryV3();
        return;
    }

    updateCheckoutTotalV3(method.price);
    showCheckoutV3(`
        <div class="checkout-title">📍 ${escapeHtml(method.title)}</div>
        <input id="delivery-address" class="checkout-input" type="text" placeholder="Адрес или пункт получения">
        <div class="checkout-actions">
            <button type="button" class="order-btn" id="checkout-submit">Оформить заказ</button>
            <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
        </div>
        <div id="checkout-error" class="checkout-error"></div>
    `);
    bindAddressSubmitV3();
}

function renderRussiaPointV3() {
    const form = document.getElementById('delivery-point-form');
    if (!form || !checkoutState.service) return;

    form.innerHTML = `
        <div class="checkout-title" style="margin-top:10px;">📍 Адрес ПВЗ</div>
        <input id="delivery-address" class="checkout-input" type="text" placeholder="Адрес выбранного ПВЗ" autocomplete="street-address">
        <button type="button" class="order-btn" id="checkout-submit">Оформить заказ</button>
        <div id="checkout-error" class="checkout-error"></div>
    `;
    bindAddressSubmitV3();
}

function renderAbroadCountryV3() {
    const countries = getCountriesV3();
    const countryButtons = countries.map(country => `
        <button type="button" class="checkout-country-item" data-country="${escapeHtml(country)}">${escapeHtml(country)}</button>
    `).join('');

    showCheckoutV3(`
        <div class="checkout-title">🌍 Выберите страну</div>
        <div class="checkout-summary">Доставка за рубеж: <b>договорная</b></div>
        <input id="country-search" class="checkout-country-search" type="search" placeholder="🔍 Быстрый поиск страны">
        <div id="country-list" class="checkout-country-list">${countryButtons}</div>
        <div id="selected-country" class="checkout-summary"></div>
        <div class="checkout-actions">
            <button type="button" class="order-btn" id="checkout-submit" disabled>Оформить заказ</button>
            <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
        </div>
    `);

    const search = document.getElementById('country-search');
    const list = document.getElementById('country-list');
    const submit = document.getElementById('checkout-submit');
    const selected = document.getElementById('selected-country');

    function applyCountryFilter() {
        const query = String(search?.value || '').trim().toLowerCase();
        list?.querySelectorAll('[data-country]').forEach(button => {
            button.style.display = !query || button.dataset.country.toLowerCase().includes(query) ? '' : 'none';
        });
    }

    search?.addEventListener('input', applyCountryFilter);

    list?.querySelectorAll('[data-country]').forEach(button => {
        button.addEventListener('click', () => {
            checkoutState.country = button.dataset.country || '';
            selected.innerText = `Выбрано: ${checkoutState.country}`;
            submit.disabled = !checkoutState.country;
        });
    });

    submit?.addEventListener('click', submitCheckoutV3);
    bindCheckoutBackV3();
}

function bindAddressSubmitV3() {
    document.getElementById('checkout-submit')?.addEventListener('click', submitCheckoutV3);
    bindCheckoutBackV3();
}

function bindCheckoutSubmitV3() {
    document.getElementById('checkout-submit')?.addEventListener('click', submitCheckoutV3);
    bindCheckoutBackV3();
}

function bindCheckoutBackV3() {
    document.getElementById('checkout-back')?.addEventListener('click', openDeliveryCheckoutV3);
}

function submitCheckoutV3() {
    const method = checkoutState?.method;
    if (!method) return;

    checkoutState.address = String(document.getElementById('delivery-address')?.value || '').trim();
    const errorEl = document.getElementById('checkout-error');

    if ((method.id === 'courier_ekb' || method.id === 'russia') && checkoutState.address.length < 3) {
        if (errorEl) errorEl.innerText = method.id === 'russia' ? 'Укажите адрес ПВЗ.' : 'Укажите адрес доставки.';
        return;
    }

    if (method.id === 'abroad' && !checkoutState.country) return;

    checkoutState.delivery = {
        method_id: method.id,
        method_title: method.title,
        price: method.price,
        service_id: checkoutState.service?.id || '',
        service_title: checkoutState.service?.title || '',
        country: checkoutState.country || '',
        address: checkoutState.address || ''
    };

    postOrderV3();
}

function sendOrder() {
    if (!cart.length) return;

    if (methodsNeedDeliveryV3()) {
        openDeliveryCheckoutV3().catch(error => {
            console.error('Ошибка загрузки доставки:', error);
            showCheckoutV3(`<div class="checkout-error">Не удалось загрузить способы доставки.<br>${escapeHtml(error?.message || error)}</div>`);
        });
        return;
    }

    checkoutState = {delivery: null};
    postOrderV3();
}

async function postOrderV3() {
    if (!tg?.initData) {
        alert('Заказ можно оформить только внутри Telegram.');
        return;
    }

    const productTotal = productsTotalV3();
    const delivery = checkoutState?.delivery || null;

    const payload = {
        action: 'create-order',
        initData: tg.initData,
        items: cart.map(item => `${item.name} (x${item.count})`).join(', '),
        products: cart.map(item => ({
            id: item.id,
            name: item.name,
            quantity: item.count,
            category: item.category,
            price: Number(item.price || 0)
        })),
        total: productTotal,
        needs_delivery: Boolean(delivery),
        delivery
    };

    const submit = document.getElementById('checkout-submit');
    if (submit) submit.disabled = true;

    try {
        const response = await fetch(ORDERS_API_URL, {
            method: 'POST',
            headers: {'Content-Type': 'text/plain;charset=utf-8'},
            body: JSON.stringify(payload),
            cache: 'no-store'
        });

        if (!response.ok) throw new Error(`Orders вернул HTTP ${response.status}`);

        const result = await response.json();
        if (!result?.ok) throw new Error(result?.error || 'Не удалось создать заказ.');

        tg.close();
    } catch (error) {
        console.error('Ошибка отправки заказа:', error);
        const errorEl = document.getElementById('checkout-error');
        if (errorEl) errorEl.innerText = error?.message || 'Не удалось оформить заказ. Попробуйте ещё раз.';
        const button = document.getElementById('checkout-submit');
        if (button) button.disabled = false;
    }
}

function resetCheckoutOnCartRenderV3() {
    if (!checkoutState) return;
    const block = document.getElementById('cart-checkout');
    if (block?.hidden === false) return;
}

const previousRenderCartV3 = renderCart;
renderCart = function() {
    previousRenderCartV3();
    if (!checkoutState) {
        const block = document.getElementById('cart-checkout');
        if (block) {
            block.hidden = true;
            block.innerHTML = '';
        }
        const totalLine = document.getElementById('cart-total-line');
        if (totalLine) totalLine.style.display = '';
        return;
    }
};

// Первый рендер новых элементов после загрузки каталога.
const previousToggleCartV3 = toggleCart;
toggleCart = function() {
    previousToggleCartV3();
    if (document.getElementById('cart-modal')?.style.display !== 'block') {
        hideCheckoutV3();
    }
};
