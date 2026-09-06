const SHEET_ID = '1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk';
const SHEET_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json`;

const tg = window.Telegram?.WebApp;
if (tg) tg.expand();

let products = [];
let cart = [];
let currentCategory = 'all';

function showError(message) {
    const container = document.getElementById('products');
    if (!container) return;
    container.innerHTML = `<div style="padding:20px;font-family:sans-serif;text-align:center;">
        <h3>Не удалось загрузить товары</h3>
        <p style="opacity:.75">${escapeHtml(message)}</p>
        <button onclick="loadProducts()">Повторить</button>
    </div>`;
}

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
}

function getImageSrc(value) {
    const image = String(value ?? '').trim();
    if (!image) return 'images/placeholder.jpg';
    if (/^(https?:)?\\//i.test(image) || image.startsWith('data:')) return image;
    return `images/${encodeURIComponent(image)}`;
}

async function loadProducts() {
    const container = document.getElementById('products');
    if (container) container.innerHTML = '<div style="padding:20px;text-align:center;">Загрузка товаров...</div>';

    try {
        const response = await fetch(SHEET_URL, { cache: 'no-store' });
        if (!response.ok) throw new Error(`Google Sheets ответил ${response.status}`);

        const text = await response.text();
        const jsonStart = text.indexOf('{');
        const jsonEnd = text.lastIndexOf('}');
        if (jsonStart < 0 || jsonEnd < jsonStart) throw new Error('Google Sheets не вернул данные в формате JSON. Проверь публикацию таблицы в интернете.');

        const json = JSON.parse(text.slice(jsonStart, jsonEnd + 1));
        if (!json.table || !Array.isArray(json.table.rows)) throw new Error('В ответе Google Sheets нет строк товаров.');

        products = json.table.rows.map((row, index) => {
            const cells = row.c || [];
            return {
                id: cells[0]?.v ?? index,
                name: cells[1]?.v ?? 'Без названия',
                price: Number(cells[2]?.v ?? 0) || 0,
                category: String(cells[3]?.v ?? 'items').trim().toLowerCase(),
                description: String(cells[4]?.v ?? ''),
                image: String(cells[5]?.v ?? 'placeholder.jpg')
            };
        }).filter(p => p.name && p.name !== 'Без названия' || p.price !== 0 || p.description);

        render();
    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
        showError(error?.message || 'Неизвестная ошибка');
    }
}

function render() {
    const container = document.getElementById('products');
    if (!container) return;

    const search = (document.getElementById('search')?.value || '').toLowerCase().trim();
    const sortBy = document.getElementById('sort')?.value || 'default';

    let filtered = products
        .filter(p => currentCategory === 'all' || p.category === currentCategory)
        .filter(p => p.name.toLowerCase().includes(search) || p.description.toLowerCase().includes(search));

    if (sortBy === 'low') filtered.sort((a, b) => a.price - b.price);
    if (sortBy === 'high') filtered.sort((a, b) => b.price - a.price);

    if (!filtered.length) {
        container.innerHTML = '<div style="padding:20px;text-align:center;opacity:.7;">Товары не найдены</div>';
        return;
    }

    container.innerHTML = filtered.map(p => {
        const images = p.image.split(',').map(x => x.trim()).filter(Boolean);
        const imagesHtml = images.length > 1
            ? `<div class="product-gallery">${images.map(img => `<img src="${escapeHtml(getImageSrc(img))}" class="gallery-img" loading="lazy" onerror="this.src='images/placeholder.jpg'"></div>`).join('')}`
            : `<img src="${escapeHtml(getImageSrc(images[0] || 'placeholder.jpg'))}" class="main-img" loading="lazy" onerror="this.src='images/placeholder.jpg'">`;

        return `<div class="product-card">
            ${imagesHtml}
            <h4>${escapeHtml(p.name)}</h4>
            <p style="font-size:11px;opacity:.8;flex-grow:1;">${escapeHtml(p.description)}</p>
            <p style="margin:5px 0;"><b>${p.price} ₽</b></p>
            <button onclick="addToCart(${JSON.stringify(p.id)})">В корзину</button>
        </div>`;
    }).join('');
}

function filterCategory(cat, event) {
    currentCategory = cat;
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    if (event?.currentTarget) event.currentTarget.classList.add('active');
    render();
}

function addToCart(id) {
    const prod = products.find(p => String(p.id) === String(id));
    if (!prod) return;
    const inCart = cart.find(item => String(item.id) === String(id));
    if (inCart) inCart.count++;
    else cart.push({ ...prod, count: 1 });
    updateCartButton();
}

function updateCartButton() {
    const el = document.getElementById('cart-count');
    if (el) el.innerText = cart.reduce((sum, item) => sum + item.count, 0);
}

function toggleCart() {
    const modal = document.getElementById('cart-modal');
    if (!modal) return;
    modal.style.display = modal.style.display === 'block' ? 'none' : 'block';

    const itemsDiv = document.getElementById('cart-items');
    if (!itemsDiv) return;
    let total = 0;
    itemsDiv.innerHTML = cart.map(item => {
        const itemTotal = item.price * item.count;
        total += itemTotal;
        return `<p><b>${escapeHtml(item.name)}</b> x${item.count} — ${itemTotal} ₽</p>`;
    }).join('') || '<p>Корзина пуста</p>';

    document.getElementById('cart-total').innerText = total;
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
        alert(`Заказ: ${itemsText}\nИтого: ${total} ₽`);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('search')?.addEventListener('input', render);
    document.getElementById('sort')?.addEventListener('change', render);
    loadProducts();
});
