const SHEET_ID = '1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk';

// Берём данные из таблицы.
// G:J — ссылки на фотографии.
// K:N — картинки внутри Google Таблиц, сайту они не нужны.
const SHEET_URL =
    `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json`;

const STOCK_API_URL =
    'https://script.google.com/macros/s/AKfycbwwQkE9C1U82T0LoYv9umYrc-pmeD0KSZP0IOWAtEvWrKGagUNPJeoUvtIyviQF4-vfoTg/exec';

const tg = window.Telegram?.WebApp;

if (tg) {
    tg.expand();
}

let products = [];
let cart = [];
let currentCategory = 'all';

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatPrice(value) {
    return new Intl.NumberFormat('ru-RU').format(Number(value) || 0);
}

function parseBalance(value) {
    const text = String(value ?? '').trim();
    if (text === '∞' || text.toLowerCase() === 'infinity') return Infinity;
    const number = Number(text);
    if (!Number.isInteger(number) || number < 0) return 0;
    return number;
}

function getStockText(product) {
    if (product.balance === Infinity) return 'В наличии';
    if (product.balance <= 0) return 'Нет в наличии';
    return `В наличии: ${product.balance} шт.`;
}

function parseGvizResponse(text) {
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

function getImageUrl(image) {
    const value = String(image || '').trim();
    if (!value || value.toLowerCase() === 'image') return 'images/placeholder.jpg';
    if (/^(https?:)?\/\//i.test(value) || value.startsWith('data:')) return value;
    return `images/${encodeURIComponent(value)}`;
}

function getProductImages(product) {
    return [product.image, product.image2, product.image3, product.image4]
        .map(value => String(value || '').trim())
        .filter(value => value && value.toLowerCase() !== 'image');
}

function showLoadError(error) {
    const container = document.getElementById('products');
    if (!container) return;
    const message = error?.message || String(error) || 'Неизвестная ошибка';
    container.innerHTML = `<div class="load-error"><h3>Не удалось загрузить товары</h3><p>${escapeHtml(message)}</p><button type="button" onclick="loadProducts()">Повторить</button></div>`;
}

async function loadProducts() {
    const container = document.getElementById('products');
    if (container) container.innerHTML = '<div class="loading">Загрузка товаров...</div>';
    try {
        const response = await fetch(SHEET_URL, { method: 'GET', cache: 'no-store' });
        if (!response.ok) throw new Error(`Google Sheets вернул HTTP ${response.status}`);
        const text = await response.text();
        const json = parseGvizResponse(text);
        if (!json.table || !Array.isArray(json.table.rows)) throw new Error('В ответе Google Таблицы отсутствуют строки с товарами.');
        products = json.table.rows.map((row, index) => {
            const cells = row.c || [];
            const value = (columnIndex, fallback = '') => {
                const cell = cells[columnIndex];
                return cell && cell.v !== null && cell.v !== undefined ? cell.v : fallback;
            };
            return {
                id: value(0, index),
                name: String(value(1, 'Без названия')),
                price: Number(value(2, 0)) || 0,
                balance: parseBalance(value(3, 0)),
                category: String(value(4, 'items')).trim().toLowerCase(),
                description: String(value(5, ''),),
                image: String(value(6, '')).trim(),
                image2: String(value(7, '')).trim(),
                image3: String(value(8, '')).trim(),
                image4: String(value(9, '')).trim()
            };
        });
        console.log('Товары загружены:', products);
        render();
        updateCartButton();
    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
        showLoadError(error);
    }
}

function getCartItem(id) { return cart.find(item => String(item.id) === String(id)); }
function getCartQuantity(id) { const item = getCartItem(id); return item ? item.count : 0; }

function setCartQuantity(id, quantity) {
    const product = products.find(item => String(item.id) === String(id));
    if (!product) return;
    quantity = Math.max(0, Number(quantity) || 0);
    if (product.category !== 'items') quantity = quantity > 0 ? 1 : 0;
    if (product.balance !== Infinity) quantity = Math.min(quantity, product.balance);
    const index = cart.findIndex(item => String(item.id) === String(id));
    if (quantity <= 0) {
        if (index !== -1) cart.splice(index, 1);
    } else if (index !== -1) {
        cart[index].count = quantity;
    } else {
        cart.push({ ...product, count: quantity });
    }
    updateCartButton();
    updateProductCard(id);
}

function addToCart(id) {
    const product = products.find(item => String(item.id) === String(id));
    if (!product) return;
    const current = getCartQuantity(id);
    if (product.balance !== Infinity && current >= product.balance) return;
    setCartQuantity(id, product.category === 'items' ? current + 1 : 1);
    animateCart();
}

function removeFromCart(id) { setCartQuantity(id, getCartQuantity(id) - 1); }

function updateCartButton() {
    const count = cart.reduce((sum, item) => sum + item.count, 0);
    const button = document.getElementById('cart-btn');
    const countEl = document.getElementById('cart-count');
    if (countEl) countEl.innerText = count;
    if (button) {
        button.classList.toggle('cart-empty', count === 0);
        button.classList.toggle('cart-has-items', count > 0);
    }
}

function getCardButtonHtml(product) {
    const quantity = getCartQuantity(product.id);
    if (product.balance <= 0) return `<button type="button" class="card-cart-btn" disabled>Нет в наличии</button>`;
    if (product.category !== 'items') {
        return `<button type="button" class="card-cart-btn" onclick="event.stopPropagation(); addToCart(${JSON.stringify(product.id)});">${quantity > 0 ? 'В корзине' : 'В корзину'}</button>`;
    }
    if (quantity <= 0) {
        return `<button type="button" class="card-cart-btn" onclick="event.stopPropagation(); addToCart(${JSON.stringify(product.id)});">В корзину</button>`;
    }
    const plusDisabled = product.balance !== Infinity && quantity >= product.balance;
    return `<div class="card-quantity" onclick="event.stopPropagation();"><button type="button" class="card-quantity-btn" onclick="event.stopPropagation(); removeFromCart(${JSON.stringify(product.id)});" aria-label="Уменьшить количество">−</button><span class="card-quantity-value">${quantity}</span><button type="button" class="card-quantity-btn" ${plusDisabled ? 'disabled' : ''} onclick="event.stopPropagation(); addToCart(${JSON.stringify(product.id)});" aria-label="Увеличить количество">+</button></div>`;
}

function updateProductCard(id) {
    const card = document.querySelector(`.product-card[data-product-id="${CSS.escape(String(id))}"]`);
    if (!card) return;
    const buttonArea = card.querySelector('.card-button-area');
    if (!buttonArea) return;
    const product = products.find(item => String(item.id) === String(id));
    if (!product) return;
    buttonArea.innerHTML = getCardButtonHtml(product);
}

function animateCart() {
    const button = document.getElementById('cart-btn');
    if (!button) return;
    button.classList.remove('cart-pulse');
    void button.offsetWidth;
    button.classList.add('cart-pulse');
    setTimeout(() => button.classList.remove('cart-pulse'), 450);
}

function render() {
    const container = document.getElementById('products');
    if (!container) return;
    const searchEl = document.getElementById('search');
    const sortEl = document.getElementById('sort');
    const searchTxt = (searchEl?.value || '').trim().toLowerCase();
    const sortBy = sortEl?.value || 'default';
    let filtered = products.filter(product => currentCategory === 'all' || product.category === currentCategory).filter(product => product.name.toLowerCase().includes(searchTxt) || product.description.toLowerCase().includes(searchTxt));
    if (sortBy === 'low') filtered.sort((a, b) => a.price - b.price);
    if (sortBy === 'high') filtered.sort((a, b) => b.price - a.price);
    if (!filtered.length) { container.innerHTML = '<div class="empty-products">Товаров не найдено.</div>'; return; }
    container.innerHTML = filtered.map(product => {
        const images = getProductImages(product);
        let imagesHtml = '';
        if (images.length > 1) {
            imagesHtml = `<div class="product-gallery">${images.map(src => `<img src="${escapeHtml(getImageUrl(src))}" class="gallery-img" alt="${escapeHtml(product.name)}" onerror="this.onerror=null;this.src='images/placeholder.jpg';">`).join('')}</div>`;
        } else {
            const src = images.length ? getImageUrl(images[0]) : 'images/placeholder.jpg';
            imagesHtml = `<img src="${escapeHtml(src)}" class="main-img" alt="${escapeHtml(product.name)}" onerror="this.onerror=null;this.src='images/placeholder.jpg';">`;
        }
        const stockHtml = product.category === 'items'
            ? `<p class="product-card-stock">${escapeHtml(getStockText(product))}</p>`
            : '';
        return `<div class="product-card" data-product-id="${escapeHtml(String(product.id))}" onclick="openProductModal(${JSON.stringify(product.id)})">${imagesHtml}<h4>${escapeHtml(product.name)}</h4><p class="product-card-price"><b>${formatPrice(product.price)} ₽</b></p>${stockHtml}<div class="card-button-area">${getCardButtonHtml(product)}</div></div>`;
    }).join('');
}

function filterCategory(cat, button) {
    currentCategory = cat;
    document.querySelectorAll('.cat-btn').forEach(btn => btn.classList.remove('active'));
    if (button) button.classList.add('active');
    render();
}

function toggleCart() {
    const modal = document.getElementById('cart-modal');
    if (!modal) return;
    if (modal.style.display === 'block') { modal.style.display = 'none'; return; }
    modal.style.display = 'block';
    renderCart();
}

function renderCart() {
    const itemsDiv = document.getElementById('cart-items');
    if (!itemsDiv) return;
    let total = 0;
    if (!cart.length) {
        itemsDiv.innerHTML = '<div class="empty-cart">Корзина пока пуста</div>';
    } else {
        itemsDiv.innerHTML = cart.map((item, index) => {
            total += item.price * item.count;
            if (item.category !== 'items') {
                return `<div class="cart-item" data-index="${index}" style="margin-bottom:15px;"><div><b>${escapeHtml(item.name)}</b></div><div style="display:flex;align-items:center;margin-top:8px;"><span style="margin-left:auto;">${formatPrice(item.price)} ₽</span><button type="button" class="cart-remove" data-index="${index}" style="width:40px;height:36px;margin-left:10px;">🗑️</button></div></div>`;
            }
            const plusDisabled = item.balance !== Infinity && item.count >= item.balance;
            return `<div class="cart-item" data-index="${index}" style="margin-bottom:15px;"><div style="margin-bottom:8px;"><b>${escapeHtml(item.name)}</b></div><div style="display:flex;align-items:center;gap:10px;"><button type="button" class="cart-minus" data-index="${index}" style="width:40px;height:36px;">−</button><span style="min-width:20px;text-align:center;">${item.count}</span><button type="button" class="cart-plus" data-index="${index}" ${plusDisabled ? 'disabled' : ''} style="width:40px;height:36px;">+</button><span style="margin-left:auto;">${formatPrice(item.price * item.count)} ₽</span><button type="button" class="cart-remove" data-index="${index}" style="width:40px;height:36px;">🗑️</button></div></div>`;
        }).join('');
    }
    const totalEl = document.getElementById('cart-total');
    if (totalEl) totalEl.innerText = formatPrice(total);
    updateCartButton();
    itemsDiv.querySelectorAll('.cart-minus').forEach(button => button.addEventListener('click', function() { const index = Number(this.dataset.index); if (!cart[index]) return; setCartQuantity(cart[index].id, cart[index].count - 1); renderCart(); }));
    itemsDiv.querySelectorAll('.cart-plus').forEach(button => button.addEventListener('click', function() { const index = Number(this.dataset.index); if (!cart[index]) return; addToCart(cart[index].id); renderCart(); }));
    itemsDiv.querySelectorAll('.cart-remove').forEach(button => button.addEventListener('click', function() { const index = Number(this.dataset.index); if (!cart[index]) return; setCartQuantity(cart[index].id, 0); renderCart(); }));
}

function openProductModal(id) {
    const product = products.find(item => String(item.id) === String(id));
    if (!product) return;
    const modal = document.getElementById('product-modal');
    const content = document.getElementById('product-modal-content');
    if (!modal || !content) return;
    const images = getProductImages(product);
    const imagesHtml = images.length ? `<div class="product-modal-gallery">${images.map((src, index) => `<img src="${escapeHtml(getImageUrl(src))}" alt="${escapeHtml(product.name)}" onclick="openImageLightbox(${JSON.stringify(product.id)}, ${index}); event.stopPropagation();" onerror="this.onerror=null;this.src='images/placeholder.jpg';">`).join('')}</div>` : '';
    const currentQuantity = getCartQuantity(product.id);
    const displayedQuantity = currentQuantity > 0 ? currentQuantity : product.balance > 0 ? 1 : 0;
    const plusDisabled = product.balance !== Infinity && displayedQuantity >= product.balance;
    const quantityHtml = product.category === 'items' ? `<div class="product-quantity"><button type="button" onclick="changeProductQuantity(${JSON.stringify(product.id)}, -1)">−</button><span id="product-quantity-value">${displayedQuantity}</span><button type="button" ${plusDisabled || product.balance <= 0 ? 'disabled' : ''} onclick="changeProductQuantity(${JSON.stringify(product.id)}, 1)">+</button></div>` : '';
    content.innerHTML = `${imagesHtml}<h2 class="product-modal-title">${escapeHtml(product.name)}</h2><div class="product-modal-description">${escapeHtml(product.description)}</div><div class="product-modal-price">${formatPrice(product.price)} ₽</div><div class="product-modal-stock">${escapeHtml(getStockText(product))}</div>${quantityHtml}<button type="button" class="product-add-btn" ${product.balance <= 0 ? 'disabled' : ''} onclick="addProductToCartFromModal(${JSON.stringify(product.id)})">${product.balance <= 0 ? 'Нет в наличии' : currentQuantity > 0 ? 'Добавить ещё' : 'В корзину'}</button>`;
    modal.style.display = 'block';
}

function openImageLightbox(productId, startIndex) {
    const product = products.find(item => String(item.id) === String(productId));
    if (!product) return;
    const images = getProductImages(product);
    if (!images.length) return;

    let lightbox = document.getElementById('image-lightbox');
    if (!lightbox) {
        lightbox = document.createElement('div');
        lightbox.id = 'image-lightbox';
        lightbox.className = 'image-lightbox';
        document.body.appendChild(lightbox);
    }

    lightbox.innerHTML = `<div class="image-lightbox-track">${images.map((src, index) => `<div class="image-lightbox-slide"><img src="${escapeHtml(getImageUrl(src))}" alt="${escapeHtml(product.name)}" onclick="event.stopPropagation();" onerror="this.onerror=null;this.src='images/placeholder.jpg';"></div>`).join('')}</div>`;
    lightbox.onclick = event => {
        if (event.target === lightbox || event.target.classList.contains('image-lightbox-slide')) {
            closeImageLightbox();
        }
    };
    lightbox.style.display = 'flex';
    document.body.classList.add('lightbox-open');

    const track = lightbox.querySelector('.image-lightbox-track');
    if (track) {
        const slide = track.children[Math.max(0, Math.min(Number(startIndex) || 0, images.length - 1))];
        if (slide) slide.scrollIntoView({ behavior: 'auto', block: 'nearest', inline: 'start' });
    }
}

function closeImageLightbox() {
    const lightbox = document.getElementById('image-lightbox');
    if (lightbox) lightbox.style.display = 'none';
    document.body.classList.remove('lightbox-open');
}

function closeProductModal() { const modal = document.getElementById('product-modal'); if (modal) modal.style.display = 'none'; }

function changeProductQuantity(id, delta) {
    const product = products.find(item => String(item.id) === String(id));
    if (!product || product.category !== 'items') return;
    const current = getCartQuantity(id);
    let quantity = current === 0 ? Math.max(0, delta) : current + delta;
    if (product.balance !== Infinity) quantity = Math.min(quantity, product.balance);
    setCartQuantity(id, quantity);
    const quantityEl = document.getElementById('product-quantity-value');
    if (quantityEl) quantityEl.innerText = quantity > 0 ? quantity : 0;
    if (quantity <= 0) { closeProductModal(); return; }
    const addButton = document.querySelector('.product-add-btn');
    if (addButton) addButton.innerText = 'Добавить ещё';
    const plusButton = document.querySelector('.product-quantity button:last-child');
    if (plusButton) plusButton.disabled = product.balance !== Infinity && quantity >= product.balance;
}

function addProductToCartFromModal(id) {
    const product = products.find(item => String(item.id) === String(id));
    if (!product) return;
    addToCart(id);
    const quantityEl = document.getElementById('product-quantity-value');
    if (quantityEl) quantityEl.innerText = getCartQuantity(id) || 0;
    const addButton = document.querySelector('.product-add-btn');
    if (addButton) {
        addButton.innerText = 'Добавить ещё';
        addButton.disabled = product.balance <= 0 || (product.balance !== Infinity && getCartQuantity(id) >= product.balance);
    }
}

function sendOrder() {
    if (!cart.length) return;
    const total = cart.reduce((sum, item) => sum + item.price * item.count, 0);
    const itemsText = cart.map(item => `${item.name} (x${item.count})`).join(', ');
    const payload = JSON.stringify({
        items: itemsText,
        products: cart.map(item => ({ id: item.id, quantity: item.count, category: item.category, price: item.price })),
        total: total
    });
    if (tg?.sendData) { tg.sendData(payload); tg.close(); }
    else alert('Заказ можно оформить только внутри Telegram.');
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('search')?.addEventListener('input', render);
    document.getElementById('sort')?.addEventListener('change', render);
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') closeImageLightbox();
    });
    loadProducts();
});
