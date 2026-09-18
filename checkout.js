// ==================================================
// SHOP CHECKOUT: ПОДКАТЕГОРИИ + ДОСТАВКА + ЗАКАЗ
// ==================================================

const DELIVERY_SHEET_URL_V4 =
    `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=${encodeURIComponent('Доставка')}`;

let selectedSubcategoriesV4 = new Set();
let deliveryCatalogV4 = null;
let checkoutStateV4 = null;
let postOrderStateV4 = null;

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
    .checkout-option.selected {
        background: color-mix(in srgb, var(--tg-theme-button-color, #2481cc) 16%, var(--tg-theme-secondary-bg-color, #f5f5f5));
        border-color: var(--tg-theme-button-color, #2481cc);
        box-shadow: 0 0 0 1px color-mix(in srgb, var(--tg-theme-button-color, #2481cc) 18%, transparent);
    }
    .checkout-input,
    .checkout-country-search {
        width: 100%;
        box-sizing: border-box;
        padding: 11px 12px;
        margin: 6px 0 10px;
        border-radius: 9px;
        border: 1px solid #555;
        background: #2a2a2a;
        color: #fff !important;
        caret-color: #fff;
    }
    .checkout-input::placeholder,
    .checkout-country-search::placeholder {
        color: #bdbdbd;
        opacity: 1;
    }
    .payment-info {
        margin: 8px 0 14px;
        padding: 12px 13px;
        border: 1px solid color-mix(in srgb, var(--tg-theme-button-color, #2481cc) 18%, #bbb);
        border-radius: 12px;
        background: color-mix(in srgb, var(--tg-theme-button-color, #2481cc) 5%, var(--tg-theme-bg-color, #fff));
        color: #fff;
    }
    .payment-title,
    .payment-info .payment-row,
    .payment-info .payment-row-label,
    .payment-info .payment-phone,
    .payment-info .payment-note-content {
        color: #fff !important;
    }
    .payment-title { font-weight: 700; margin-bottom: 7px; }
    .payment-row { display: flex; align-items: center; gap: 8px; margin: 5px 0; }
    .payment-row-label { min-width: 88px; }
    .payment-phone {
        flex: 1 1 auto;
        font-weight: 700;
        letter-spacing: .2px;
    }
    .copy-payment-phone {
        flex: none !important;
        width: 38px !important;
        min-width: 38px !important;
        height: 38px;
        margin: 0 !important;
        padding: 7px !important;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: var(--tg-theme-button-color, #2481cc) !important;
        color: var(--tg-theme-button-text-color, #fff) !important;
        border-radius: 9px !important;
    }
    .copy-payment-phone svg { width: 21px; height: 21px; display: block; }
    .payment-note {
        margin-top: 10px;
        border-top: 1px solid color-mix(in srgb, var(--tg-theme-button-color, #2481cc) 12%, transparent);
        padding-top: 9px;
    }
    .payment-note summary {
        cursor: pointer;
        color: #fff !important;
        font-size: 13px;
        user-select: none;
    }
    .payment-note-content {
        margin-top: 8px;
        font-size: 13px;
        line-height: 1.45;
        color: #fff !important;
    }
    .thank-you-overlay-v4 {
        position: fixed;
        inset: 0;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        box-sizing: border-box;
        background: color-mix(in srgb, var(--tg-theme-bg-color, #fff) 78%, #000);
    }
    .thank-you-card-v4 {
        width: min(320px, 88vw);
        padding: 24px 20px;
        box-sizing: border-box;
        border-radius: 18px;
        text-align: center;
        background: var(--tg-theme-secondary-bg-color, #f5f5f5);
        color: var(--tg-theme-text-color, #000);
        box-shadow: 0 12px 40px rgba(0,0,0,.22);
    }
    .thank-you-title-v4 { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
    .thank-you-text-v4 { font-size: 14px; line-height: 1.45; margin-bottom: 18px; }
    .thank-you-button-v4 {
        width: 72px;
        height: 72px;
        padding: 0;
        border: none;
        border-radius: 16px;
        background: var(--tg-theme-button-color, #2481cc);
        color: var(--tg-theme-button-text-color, #fff);
        font-size: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 14px color-mix(in srgb, var(--tg-theme-button-color, #2481cc) 35%, transparent);
        cursor: pointer;
    }
    .thank-you-button-v4:active { transform: scale(.96); }
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
    .post-order-block,
    .contact-choice-block { margin-top: 8px; }
    .post-order-option,
    .contact-choice-option { width: 100%; margin: 6px 0; padding: 12px; border: 1px solid color-mix(in srgb, var(--tg-theme-button-color, #2481cc) 22%, transparent); border-radius: 10px; background: var(--tg-theme-secondary-bg-color, #f5f5f5); color: var(--tg-theme-text-color, #000); text-align: left; }
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

function setMainCartOrderButtonHiddenV4(hidden) {
    const button = document.getElementById('cart-order-btn');
    if (button) button.hidden = hidden;
}

function showCheckoutV4(content) {
    const block = document.getElementById('cart-checkout');
    if (!block) return;
    block.hidden = false;
    block.innerHTML = content;
    setMainCartOrderButtonHiddenV4(true);
}

function hideCheckoutV4() {
    const block = document.getElementById('cart-checkout');
    if (block) {
        block.hidden = true;
        block.innerHTML = '';
    }
    setMainCartOrderButtonHiddenV4(false);
    checkoutStateV4 = null;
    postOrderStateV4 = null;
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
            <div id="checkout-error" class="checkout-error"></div>
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
                document.querySelectorAll('[data-delivery-service]').forEach(item => item.classList.toggle(
                    'selected',
                    item.dataset.deliveryService === checkoutStateV4.service?.id
                ));
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
        <div id="checkout-error" class="checkout-error"></div>
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

    showPostOrderV4();
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
    showPostOrderV4();
}

function getOrderKindV4() {
    const managedCategories = new Set(['repeat', 'service']);
    const managedCount = cart.filter(item =>
        managedCategories.has(String(item.category || '').trim().toLowerCase())
    ).length;

    return {
        managedOrder: cart.length > 0 && managedCount === cart.length,
        mixedOrder: managedCount > 0 && managedCount < cart.length
    };
}

function showPostOrderV4() {
    const kind = getOrderKindV4();
    const hasItems = cart.some(item => String(item.category || '').trim().toLowerCase() === 'items');

    postOrderStateV4 = {
        action: kind.managedOrder ? 'managed' : (!hasItems ? 'wait_manager' : null),
        contactMethod: null,
        busy: false
    };

    if (kind.managedOrder) {
        showContactChoiceV4('⚒️ Этот заказ требует согласования с мастером.\n\nКак с вами связаться?');
        return;
    }

    if (!hasItems) {
        showContactChoiceV4('⚒️ Этот заказ требует согласования с мастером.\n\nКак с вами связаться?');
        return;
    }

    const mixedHint = kind.mixedOrder
        ? '<div class="checkout-summary">⚒️ Часть заказа требует согласования с мастером.</div>'
        : '';

    const paymentBlock = `
        <div class="payment-info">
            <div class="payment-title">💳 Оплата переводом</div>
            <div class="payment-row">
                <span class="payment-row-label">Телефон</span>
                <span class="payment-phone" id="payment-phone-number">+79089147913</span>
                <button type="button" class="order-btn copy-payment-phone" id="copy-payment-phone" aria-label="Скопировать номер" title="Скопировать номер">${getCopyIconV4()}</button>
            </div>
            <div class="payment-row">
                <span class="payment-row-label">Банк</span>
                <span>Сбербанк</span>
            </div>
            <div class="payment-row">
                <span class="payment-row-label">Получатель</span>
                <span>Лия П.</span>
            </div>
            <div class="payment-row">
                <span class="payment-row-label">К оплате</span>
                <span><b>${formatPrice(payableNowTotalV4())} ₽</b></span>
            </div>
            <details class="payment-note">
                <summary>Почему перевод</summary>
                <div class="payment-note-content">Я работаю как самозанятая, поэтому принимаю оплату переводом. Чек выдается лично или в Telegram. Спасибо за понимание!</div>
            </details>
        </div>
    `;

    showCheckoutV4(`
        <div class="checkout-title">✅ Заказ готов</div>
        <div class="checkout-summary">Здесь можно выбрать, что делать дальше.</div>
        ${paymentBlock}
        ${mixedHint}
        <button type="button" class="post-order-option" id="post-order-paid">💳 <b>Я оплатил</b></button>
        <button type="button" class="post-order-option" id="post-order-manager">⏳ <b>Подожду мастера</b></button>
    `);

    document.getElementById('copy-payment-phone')?.addEventListener('click', copyPaymentPhoneV4);

    document.getElementById('post-order-paid')?.addEventListener('click', () => {
        postOrderStateV4.action = 'paid';
        showContactChoiceV4('Как с вами связаться?');
    });

    document.getElementById('post-order-manager')?.addEventListener('click', () => {
        postOrderStateV4.action = 'wait_manager';
        showContactChoiceV4('Как с вами связаться?');
    });
}

function showContactChoiceV4(title) {
    if (!postOrderStateV4 || postOrderStateV4.busy) return;

    const username = String(tg?.initDataUnsafe?.user?.username || '').trim();

    showCheckoutV4(`
        <div class="contact-choice-block">
            <div class="checkout-title">${escapeHtml(title || 'Как с вами связаться?')}</div>
            <div class="checkout-summary">Выберите удобный способ связи.</div>
            <button type="button" class="contact-choice-option" id="contact-telegram">💬 Telegram</button>
            <button type="button" class="contact-choice-option" id="contact-phone">📱 Телефон</button>
            <div id="checkout-error" class="checkout-error"></div>
        </div>
    `);

    document.getElementById('contact-telegram')?.addEventListener('click', () => {
        if (!username) {
            showTelegramUsernameRequiredV4();
            return;
        }
        postOrderStateV4.contactMethod = 'telegram';
        sendCompleteOrderV4();
    });

    document.getElementById('contact-phone')?.addEventListener('click', () => {
        requestPhoneV4();
    });
}

function showTelegramUsernameRequiredV4() {
    showCheckoutV4(`
        <div class="checkout-title">💬 Telegram</div>
        <div class="checkout-summary">Чтобы связаться с вами через Telegram, добавьте, пожалуйста, @username в настройках Telegram.</div>
        <div class="checkout-actions"><button type="button" class="order-btn" id="contact-username-ok">ОК</button></div>
    `);
    document.getElementById('contact-username-ok')?.addEventListener('click', () => showContactChoiceV4('Как с вами связаться?'));
}

function requestPhoneV4() {
    if (!tg?.requestContact) {
        showCheckoutV4(`
            <div class="checkout-error">Telegram не поддерживает запрос номера телефона в этой версии клиента.</div>
            <div class="checkout-actions"><button type="button" class="order-btn" id="contact-phone-back">Назад</button></div>
        `);
        document.getElementById('contact-phone-back')?.addEventListener('click', () => showContactChoiceV4('Как с вами связаться?'));
        return;
    }

    tg.requestContact(function(shared) {
        if (shared) {
            postOrderStateV4.contactMethod = 'phone';
            sendCompleteOrderV4();
            return;
        }

        showContactChoiceV4('Как с вами связаться?');
    });
}

function copyPaymentPhoneV4(button) {
    const phone = '+79089147913';
    const markCopied = () => {
        if (!button) return;
        const original = button.innerText;
        button.innerText = '✓ Скопировано';
        setTimeout(() => { button.innerText = original; }, 1800);
    };

    if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(phone)
            .then(markCopied)
            .catch(() => {
                try {
                    const area = document.createElement('textarea');
                    area.value = phone;
                    area.style.position = 'fixed';
                    area.style.opacity = '0';
                    document.body.appendChild(area);
                    area.select();
                    document.execCommand('copy');
                    area.remove();
                    markCopied();
                } catch (error) {
                    console.warn('Не удалось скопировать номер:', error);
                }
            });
        return;
    }

    try {
        const area = document.createElement('textarea');
        area.value = phone;
        area.style.position = 'fixed';
        area.style.opacity = '0';
        document.body.appendChild(area);
        area.select();
        document.execCommand('copy');
        area.remove();
        markCopied();
    } catch (error) {
        console.warn('Не удалось скопировать номер:', error);
    }
}

function buildCompleteOrderPayloadV4() {
    const delivery = checkoutStateV4?.delivery || null;
    return {
        action: 'create-order',
        initData: tg?.initData || '',
        items: cart.map(item => `${item.name} (x${item.count})`).join(', '),
        products: cart.map(item => ({
            name: item.name,
            quantity: item.count,
            category: item.category,
            price: Number(item.price || 0)
        })),
        total: productsTotalV4(),
        needs_delivery: Boolean(delivery),
        delivery,
        post_order_action: postOrderStateV4?.action || 'wait_manager',
        contact_method: postOrderStateV4?.contactMethod || ''
    };
}

function showThankYouPopupV4() {
    const closeApp = () => {
        try { tg.close(); }
        catch (error) { console.warn('Не удалось закрыть Mini App:', error); }
    };

    if (tg?.showPopup) {
        tg.showPopup({
            title: 'Спасибо за заказ!',
            message: 'Всё записал и передал мастеру.',
            buttons: [{id: 'done', type: 'default', text: '🤝'}]
        }, closeApp);
        return;
    }

    showCheckoutV4(`
        <div class="checkout-title">Спасибо за заказ! 🤝</div>
        <div class="checkout-summary">Всё записал и передал мастеру.</div>
        <button type="button" class="order-btn" id="thank-you-close">🤝</button>
    `);
    document.getElementById('thank-you-close')?.addEventListener('click', closeApp);
}

function sendCompleteOrderV4() {
    if (!tg?.initData || !postOrderStateV4 || postOrderStateV4.busy) return;

    postOrderStateV4.busy = true;
    const body = JSON.stringify(buildCompleteOrderPayloadV4());

    let handedOff = false;
    try {
        if (navigator.sendBeacon) {
            handedOff = navigator.sendBeacon(
                ORDERS_API_URL,
                new Blob([body], {type: 'text/plain;charset=UTF-8'})
            );
        }
    } catch (error) {
        console.warn('Не удалось передать заказ через sendBeacon:', error);
    }

    if (!handedOff) {
        try {
            fetch(ORDERS_API_URL, {
                method: 'POST',
                headers: {'Content-Type': 'text/plain;charset=utf-8'},
                body,
                cache: 'no-store',
                keepalive: true
            }).catch(error => console.error('Ошибка фоновой отправки заказа:', error));
        } catch (error) {
            console.error('Не удалось запустить фоновую отправку заказа:', error);
        }
    }

    showThankYouPopupV4();
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
