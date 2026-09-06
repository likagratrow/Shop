const SHEET_ID = '1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk';
const SHEET_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json`;

const tg = window.Telegram?.WebApp;
if (tg) tg.expand();

let products = [];
let cart = [];
let currentCategory = 'all';

function showLoadError(error) {
    const container = document.getElementById('products');
    if (!container) return;

    const message = error?.message || String(error) || 'Неизвестная ошибка';
    container.innerHTML = `
        <div class="load-error">
            <h3>Не удалось загрузить товары</h3>
            <p>${escapeHtml(message)}</p>
            <button type="button" onclick="loadProducts()">Повторить</button>
        </div>
    `;
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function parseGvizResponse(text) {
    // Google Visualization API returns JSON wrapped in a function call.
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start === -1 || end === -1 || end <= start) {
        throw new Error('Google Таблица не вернула данные. Проверьте публикацию таблицы в интернете.');
    }

    try {
        return JSON.parse(text.slice(start, end + 1));
    } catch {
        throw new Error('Не удалось разобрать ответ Google Таблицы.');
    }
}

async function loadProducts() {
    const container = document.getElementById('products');
    if (container) container.innerHTML = '<div class="loading">Загрузка товаров...</div>';

    try {
        const response = await fetch(SHEET_URL, {
            method: 'GET',
            cache: 'no-store'
        });

        if (!response.ok) {
            throw new Error(`Google Sheets вернул HTTP ${response.status}`);
        }

        const text = await response.text();
        const json = parseGvizResponse(text);

        if (!json.table || !Array.isArray(json.table.rows)) {
            throw new Error('В ответе Google Таблицы отсутствуют строки с товарами.');
        }

        products = json.table.rows.map((row, index) => {
            const cells = row.c || [];
            const value = (columnIndex, fallback = '') =>
                cells[columnIndex] && cells[columnIndex].v !== null && cells[columnIndex].v !== undefined
                    ? cells[columnIndex].v
                    : fallback;

            return {
                id: value(0, index),
                name: String(value(1, 'Без названия')),
                price: Number(value(2, 0)) || 0,
                category: String(value(3, 'items')).trim().toLowerCase(),
                description: String(value(4, '')),
                image: String(value(5, 'placeholder.jpg'))
            };
        });

        render();
    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
        showLoadError(error);
    }
}

function render() {
    const container = document.getElementById('products');
    if (!container) return;

    const searchEl = document.getElementById('search');
    const sortEl = document.getElementById('sort');
    const searchTxt = (searchEl?.value || '').trim().toLowerCase();
    const sortBy = sortEl?.value || 'default';

    let filtered = products
        .filter(p => currentCategory === 'all' || p.category === currentCategory)
        .filter(p =>
            p.name.toLowerCase().includes(searchTxt) ||
            p.description.toLowerCase().includes(searchTxt)
        );

    if (sortBy === 'low') filtered.sort((a, b) => a.price - b.price);
    if (sortBy === 'high') filtered.sort((a, b) => b.price - a.price);

    if (!filtered.length) {
        container.innerHTML = '<div class="empty-products">Товаров не найдено.</div>';
        return;
    }

    container.innerHTML = filtered.map(p => {
        const images = p.image.split(',').map(s => s.trim()).filter(Boolean);
        const imagesHtml = images.length > 1
            ? `<div class="product-gallery">${images.map(src => `<img src="${getImageUrl(src)}" class="gallery-img" alt="${escapeHtml(p.name)}" onerror="this.src='images/placeholder.jpg'"></div>`).join('')}`
            : `<img src="${getImageUrl(images[0] || 'placeholder.jpg')}" class="main-img" alt="${escapeHtml(p.name)}" onerror="this.src='images/placeholder.jpg'">`;

        return `
            <div class="product-card">
                ${imagesHtml}
                <h4>${escapeHtml(p.name)}</h4>
                <p style="font-size:11px; opacity:0.8; flex-grow:1;">${escapeHtml(p.description)}</p>
                <p style="margin:5px 0;"><b>${formatPrice(p.price)} ₽</b></p>
                <button type="button" onclick="addToCart(${JSON.stringify(p.id)})">В корзину</button>
            </div>
        `;
    }).join('');
}

function getImageUrl(image) {
    const value = String(image || '').trim();
    if (/^(https?:)?\/\//i.test(value) || value.startsWith('data:')) return value;
    return `images/${encodeURIComponent(value)}`;
}

function formatPrice(value) {
    return new Intl.NumberFormat('ru-RU').format(Number(value) || 0);
}

function filterCategory(cat, button) {
    currentCategory = cat;
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    if (button) button.classList.add('active');
    render();
}

function addToCart(id) {
    const product = products.find(p => String(p.id) === String(id));
    if (!product) return;

    const inCart = cart.find(item => String(item.id) === String(id));
    if (inCart) inCart.count++;
    else cart.push({ ...product, count: 1 });

    updateCartButton();
}

function updateCartButton() {
    const count = cart.reduce((sum, item) => sum + item.count, 0);
    const el = document.getElementById('cart-count');
    if (el) el.innerText = count;
}

function toggleCart() {
    const modal = document.getElementById('cart-modal');

    if (!modal) return;

    if (modal.style.display === 'block') {
        modal.style.display = 'none';
    } else {
        modal.style.display = 'block';
        renderCart();
    }
}

function renderCart() {
    const itemsDiv = document.getElementById('cart-items');

    if (!itemsDiv) return;

    itemsDiv.innerHTML = '';

    let total = 0;

    if (!cart.length) {
        itemsDiv.innerHTML = '<p style="text-align:center;">Корзина пуста.</p>';
    } else {
        cart.forEach(item => {
            total += item.price * item.count;

            itemsDiv.innerHTML += `
                <div style="padding:10px 0; border-bottom:1px solid #ddd;">
                    
                    <div style="margin-bottom:8px;">
                        <b>${escapeHtml(item.name)}</b>
                    </div>

                    <div style="display:flex; align-items:center; gap:8px;">
                        
                        <button
                            type="button"
                            onclick="changeCartQuantity(${JSON.stringify(item.id)}, -1)"
                            style="width:35px; height:35px; font-size:20px;"
                        >−</button>

                        <span style="min-width:25px; text-align:center;">
                            ${item.count}
                        </span>

                        <button
                            type="button"
                            onclick="changeCartQuantity(${JSON.stringify(item.id)}, 1)"
                            style="width:35px; height:35px; font-size:20px;"
                        >+</button>

                        <span style="margin-left:auto;">
                            <b>${formatPrice(item.price * item.count)} ₽</b>
                        </span>

                        <button
                            type="button"
                            onclick="removeFromCart(${JSON.stringify(item.id)})"
                            style="border:none; background:none; font-size:20px; padding:5px;"
                            title="Удалить"
                        >🗑️</button>

                    </div>
                </div>
            `;
        });
    }

    const totalEl = document.getElementById('cart-total');

    if (totalEl) {
        totalEl.innerText = formatPrice(total);
    }

    updateCartButton();
}

function sendOrder() {
    if (!cart.length) return;

    const total = cart.reduce((sum, item) => sum + item.price * item.count, 0);
    const itemsText = cart.map(item => `${item.name} (x${item.count})`).join(', ');
    const payload = JSON.stringify({ items: itemsText, total });

    if (tg?.sendData) {
        tg.sendData(payload);
        tg.close();
    } else {
        alert('Заказ можно оформить только внутри Telegram.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('search')?.addEventListener('input', render);
    document.getElementById('sort')?.addEventListener('change', render);
    loadProducts();
});
