// ==================================================
// SHOP CHECKOUT: ПОДКАТЕГОРИИ + ДОСТАВКА + ORDERS
// ==================================================

const DELIVERY_SHEET_URL_V4 =
    `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=${encodeURIComponent('Доставка')}`;

let selectedSubcategoriesV4 = new Set();
let deliveryCatalogV4 = null;
let checkoutStateV4 = null;

const previousRenderV4 = render;
const previousFilterCategoryV4 = filterCategory;
const previousLoadProductsV4 = loadProducts;

// --------------------------------------------------
// ПОДКАТЕГОРИИ
// --------------------------------------------------

function getCurrentSubcategoryValuesV4() {
    if (currentCategory === 'all') return [];

    const values = [];
    const seen = new Set();

    products
        .filter(product => product.category === currentCategory)
        .forEach(product => {
            const label = String(product.subcategory || '').trim();
            const key = label.toLowerCase();
            if (!key || seen.has(key)) return;
            seen.add(key);
            values.push({key, label});
        });

    return values.sort((a, b) => a.label.localeCompare(b.label, 'ru', {sensitivity: 'base'}));
}

function renderSubcategoryFiltersV4() {
    const container = document.getElementById('subcategory-filters');
    if (!container) return;

    const values = getCurrentSubcategoryValuesV4();

    if (!values.length) {
        container.hidden = true;
        container.innerHTML = '';
        selectedSubcategoriesV4.clear();
        return;
    }

    const allowedKeys = new Set(values.map(item => item.key));
    selectedSubcategoriesV4 = new Set(
        [...selectedSubcategoriesV4].filter(key => allowedKeys.has(key))
    );

    const allChecked = selectedSubcategoriesV4.size === 0;

    container.innerHTML = `
        <div class="subcategory-filter-title">Подкатегория</div>
        <label class="subcategory-option">
            <input type="checkbox" data-subcategory="all" ${allChecked ? 'checked' : ''}>
            <span>Все</span>
        </label>
        ${values.map(item => `
            <label class="subcategory-option">
                <input type="checkbox" data-subcategory="${escapeHtml(item.key)}" ${selectedSubcategoriesV4.has(item.key) ? 'checked' : ''}>
                <span>${escapeHtml(item.label)}</span>
            </label>
        `).join('')}
    `;

    container.hidden = false;

    container.querySelectorAll('input[data-subcategory]').forEach(input => {
        input.addEventListener('change', () => {
            const key = input.dataset.subcategory || 'all';

            if (key === 'all') {
                selectedSubcategoriesV4.clear();
            } else if (input.checked) {
                selectedSubcategoriesV4.add(key);
            } else {
                selectedSubcategoriesV4.delete(key);
            }

            render();
        });
    });
}

render = function() {
    const fullProducts = products;
    const selected = selectedSubcategoriesV4;

    if (currentCategory !== 'all' && selected.size > 0) {
        products = fullProducts.filter(product =>
            product.category === currentCategory &&
            selected.has(String(product.subcategoryKey || '').trim().toLowerCase())
        );
    }

    try {
        previousRenderV4();
    } finally {
        products = fullProducts;
    }

    renderSubcategoryFiltersV4();
};

filterCategory = function(category, button) {
    selectedSubcategoriesV4.clear();
    previousFilterCategoryV4(category, button);
    renderSubcategoryFiltersV4();
};

loadProducts = async function() {
    await previousLoadProductsV4();
    renderSubcategoryFiltersV4();
};

// --------------------------------------------------
// СТИЛИ ПОДКАТЕГОРИЙ И CHECKOUT
// --------------------------------------------------

const checkoutStyleV4 = document.createElement('style');
checkoutStyleV4.textContent = `
    .subcategory-filters {
        display: flex;
        flex-wrap: wrap;
        gap: 7px 12px;
        align-items: center;
        padding: 6px 0 11px;
        margin-bottom: 4px;
    }
    .subcategory-filter-title {
        width: 100%;
        font-size: 13px;
        color: var(--tg-theme-hint-color, #888);
        margin-bottom: 1px;
    }
    .subcategory-option {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        min-height: 32px;
        font-size: 14px;
        color: var(--tg-theme-text-color, #000);
    }
    .subcategory-option input {
        accent-color: var(--tg-theme-button-color, #2481cc);
        margin: 0;
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
document.head.appendChild(checkoutStyleV4);

// --------------------------------------------------
// СТРАНЫ
// --------------------------------------------------

let countriesV4 = null;

function getCountriesV4() {
    if (countriesV4) return countriesV4;
    if (typeof Intl === 'undefined' || typeof Intl.DisplayNames !== 'function') {
        countriesV4 = [];
        return countriesV4;
    }

    const displayNames = new Intl.DisplayNames(['ru'], {type: 'region'});
    const result = [];

    for (let first = 65; first <= 90; first++) {
        for (let second = 65; second <= 90; second++) {
            const code = String.fromCharCode(first) + String.fromCharCode(second);
            try {
                const name = String(displayNames.of(code) || '').trim();
                if (!name || name.toUpperCase() === code) continue;
                result.push(name);
            } catch (_) {}
        }
    }

    countriesV4 = [...new Set(result)].sort((a, b) => a.localeCompare(b, 'ru', {sensitivity: 'base'}));
    return countriesV4;
}

// --------------------------------------------------
// ДОСТАВКА
// D = тип строки: method/service
// E = область применения служб, например russia
// Старые строки без D автоматически считаются method.
// --------------------------------------------------

async function loadDeliveryCatalogV4() {
    if (deliveryCatalogV4) return deliveryCatalogV4;

    const response = await fetch(DELIVERY_SHEET_URL_V4, {method: 'GET', cache: 'no-store'});
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

    deliveryCatalogV4 = {methods, services};
    return deliveryCatalogV4;
}

function formatDeliveryPriceV4(price) {
    return price == null ? 'договорная' : `${formatPrice(price)} ₽`;
}

function methodsNeedDeliveryV4() {
    return cart.some(item => {
        const category = String(item.category || '').trim().toLowerCase();
        return category === 'items' || category === 'repeat';
    });
}

function productsTotalV4() {
    return cart.reduce((sum, item) => sum + Number(item.price || 0) * Number(item.count || 0), 0);
}

function showCheckoutV4(content) {
    const block = document.getElementById('cart-checkout');
    if (!block) return;
    block.hidden = false;
    block.innerHTML = content;
}

function hideCheckoutV4() {
    const block = document.getElementById('cart-checkout');
    if (block) {
        block.hidden = true;
        block.innerHTML = '';
    }
    checkoutStateV4 = null;
}

function updateCheckoutTotalV4(deliveryPrice) {
    const productTotal = productsTotalV4();
    const total = deliveryPrice == null ? productTotal : productTotal + Number(deliveryPrice || 0);
    const totalEl = document.getElementById('cart-total');
    if (totalEl) totalEl.innerText = formatPrice(total);
}

async function openDeliveryCheckoutV4() {
    const catalog = await loadDeliveryCatalogV4();
    checkoutStateV4 = {method: null, service: null, country: '', address: '', delivery: null};

    const methodsHtml = catalog.methods.map(method => `
        <button type="button" class="checkout-option" data-delivery-method="${escapeHtml(method.id)}">
            <b>${escapeHtml(method.title)}</b><br>
            <small>${escapeHtml(formatDeliveryPriceV4(method.price))}</small>
        </button>
    `).join('');

    showCheckoutV4(`
        <div class="checkout-title">🚚 Выберите способ получения</div>
        <div class="checkout-summary">Товары: <b>${formatPrice(productsTotalV4())} ₽</b></div>
        ${methodsHtml || '<div class="checkout-error">В таблице «Доставка» пока нет способов получения.</div>'}
    `);

    document.querySelectorAll('[data-delivery-method]').forEach(button => {
        button.addEventListener('click', async () => {
            const method = catalog.methods.find(item => item.id === button.dataset.deliveryMethod);
            if (!method) return;
            checkoutStateV4.method = method;
            await renderDeliveryStepV4();
        });
    });
}

async function renderDeliveryStepV4() {
    const method = checkoutStateV4?.method;
    if (!method) return;

    checkoutStateV4.service = null;
    checkoutStateV4.country = '';
    checkoutStateV4.address = '';

    if (method.id === 'pickup') {
        checkoutStateV4.delivery = {
            method_id: method.id,
            method_title: method.title,
            price: method.price,
            service_id: '',
            service_title: '',
            country: '',
            address: ''
        };

        updateCheckoutTotalV4(method.price);
        showCheckoutV4(`
            <div class="checkout-title">✓ ${escapeHtml(method.title)}</div>
            <div class="checkout-summary">Стоимость доставки: <b>${escapeHtml(formatDeliveryPriceV4(method.price))}</b></div>
            <div class="checkout-actions">
                <button type="button" class="order-btn" id="checkout-submit">Оформить заказ</button>
                <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
            </div>
        `);
        bindCheckoutSubmitV4();
        return;
    }

    if (method.id === 'courier_ekb') {
        updateCheckoutTotalV4(method.price);
        showCheckoutV4(`
            <div class="checkout-title">📍 ${escapeHtml(method.title)}</div>
            <div class="checkout-summary">Стоимость доставки: <b>${escapeHtml(formatDeliveryPriceV4(method.price))}</b></div>
            <input id="delivery-address" class="checkout-input" type="text" placeholder="Улица, дом, квартира" autocomplete="street-address">
            <div class="checkout-actions">
                <button type="button" class="order-btn" id="checkout-submit">Оформить заказ</button>
                <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
            </div>
            <div id="checkout-error" class="checkout-error"></div>
        `);
        bindCheckoutSubmitV4();
        return;
    }

    if (method.id === 'russia') {
        const services = deliveryCatalogV4.services.filter(service => {
            const scopes = service.scope.split(',').map(value => value.trim()).filter(Boolean);
            return !scopes.length || scopes.includes('russia');
        });

        updateCheckoutTotalV4(method.price);
        showCheckoutV4(`
            <div class="checkout-title">📦 Сначала выберите службу доставки</div>
            <div class="checkout-summary">Доставка по РФ: <b>${escapeHtml(formatDeliveryPriceV4(method.price))}</b></div>
            <div id="delivery-services">
                ${services.map(service => `<button type="button" class="checkout-option" data-delivery-service="${escapeHtml(service.id)}">${escapeHtml(service.title)}</button>`).join('') || '<div class="checkout-error">Добавьте службы доставки на вкладку «Доставка».</div>'}
            </div>
            <div id="delivery-point-form"></div>
            <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
        `);

        document.querySelectorAll('[data-delivery-service]').forEach(button => {
            button.addEventListener('click', () => {
                checkoutStateV4.service = services.find(item => item.id === button.dataset.deliveryService) || null;
                renderRussiaPointV4();
            });
        });
        return;
    }

    if (method.id === 'abroad') {
        updateCheckoutTotalV4(null);
        renderAbroadCountryV4();
        return;
    }

    updateCheckoutTotalV4(method.price);
    showCheckoutV4(`
        <div class="checkout-title">📍 ${escapeHtml(method.title)}</div>
        <input id="delivery-address" class="checkout-input" type="text" placeholder="Адрес или пункт получения">
        <div class="checkout-actions">
            <button type="button" class="order-btn" id="checkout-submit">Оформить заказ</button>
            <button type="button" class="close-btn checkout-back" id="checkout-back">Назад</button>
        </div>
        <div id="checkout-error" class="checkout-error"></div>
    `);
    bindCheckoutSubmitV4();
}

function renderRussiaPointV4() {
    const form = document.getElementById('delivery-point-form');
    if (!form || !checkoutStateV4?.service) return;

    form.innerHTML = `
        <div class="checkout-title" style="margin-top:10px;">📍 Адрес ПВЗ</div>
        <input id="delivery-address" class="checkout-input" type="text" placeholder="Адрес выбранного ПВЗ" autocomplete="street-address">
        <button type="button" class="order-btn" id="checkout-submit">Оформить заказ</button>
        <div id="checkout-error" class="checkout-error"></div>
    `;
    bindCheckoutSubmitV4();
}

function renderAbroadCountryV4() {
    const countries = getCountriesV4();
    const countryButtons = countries.map(country => `<button type="button" class="checkout-country-item" data-country="${escapeHtml(country)}">${escapeHtml(country)}</button>`).join('');

    showCheckoutV4(`
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

    search?.addEventListener('input', () => {
        const query = String(search.value || '').trim().toLowerCase();
        list?.querySelectorAll('[data-country]').forEach(button => {
            button.style.display = !query || button.dataset.country.toLowerCase().includes(query) ? '' : 'none';
        });
    });

    list?.querySelectorAll('[data-country]').forEach(button => {
        button.addEventListener('click', () => {
            checkoutStateV4.country = button.dataset.country || '';
            selected.innerText = `Выбрано: ${checkoutStateV4.country}`;
            submit.disabled = !checkoutStateV4.country;
        });
    });

    submit?.addEventListener('click', submitCheckoutV4);
    bindCheckoutBackV4();
}

function bindCheckoutSubmitV4() {
    document.getElementById('checkout-submit')?.addEventListener('click', submitCheckoutV4);
    bindCheckoutBackV4();
}

function bindCheckoutBackV4() {
    document.getElementById('checkout-back')?.addEventListener('click', openDeliveryCheckoutV4);
}

function submitCheckoutV4() {
    const method = checkoutStateV4?.method;
    if (!method) return;

    checkoutStateV4.address = String(document.getElementById('delivery-address')?.value || '').trim();
    const errorEl = document.getElementById('checkout-error');

    if (method.id === 'courier_ekb' && checkoutStateV4.address.length < 3) {
        if (errorEl) errorEl.innerText = 'Укажите адрес доставки.';
        return;
    }

    if (method.id === 'russia' && (!checkoutStateV4.service || checkoutStateV4.address.length < 3)) {
        if (errorEl) errorEl.innerText = checkoutStateV4.service ? 'Укажите адрес ПВЗ.' : 'Выберите службу доставки.';
        return;
    }

    if (method.id === 'abroad' && !checkoutStateV4.country) return;

    checkoutStateV4.delivery = {
        method_id: method.id,
        method_title: method.title,
        price: method.price,
        service_id: checkoutStateV4.service?.id || '',
        service_title: checkoutStateV4.service?.title || '',
        country: checkoutStateV4.country || '',
        address: method.id === 'abroad' ? '' : checkoutStateV4.address || ''
    };

    postOrderV4();
}

function sendOrder() {
    if (!cart.length) return;

    if (methodsNeedDeliveryV4()) {
        openDeliveryCheckoutV4().catch(error => {
            console.error('Ошибка загрузки доставки:', error);
            showCheckoutV4(`<div class="checkout-error">Не удалось загрузить способы доставки.<br>${escapeHtml(error?.message || error)}</div>`);
        });
        return;
    }

    checkoutStateV4 = {delivery: null};
    postOrderV4();
}

async function postOrderV4() {
    if (!tg?.initData) {
        alert('Заказ можно оформить только внутри Telegram.');
        return;
    }

    const delivery = checkoutStateV4?.delivery || null;

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
        total: productsTotalV4(),
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

const previousRenderCartV4 = renderCart;
renderCart = function() {
    previousRenderCartV4();

    if (!checkoutStateV4) {
        const block = document.getElementById('cart-checkout');
        if (block) {
            block.hidden = true;
            block.innerHTML = '';
        }
    }
};

const previousToggleCartV4 = toggleCart;
toggleCart = function() {
    previousToggleCartV4();
    if (document.getElementById('cart-modal')?.style.display !== 'block') {
        hideCheckoutV4();
    }
};
