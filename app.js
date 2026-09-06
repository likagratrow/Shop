const SHEET_ID = '1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk'; 
const SHEET_URL = 'https://docs.google.com/spreadsheets/d/' + SHEET_ID + '/gviz/tq?tqx=out:json';

let tg = window.Telegram.WebApp;
tg.expand();

let products = [];
let cart = [];
let currentCategory = 'all';

async function loadProducts() {
    try {
        const response = await fetch(SHEET_URL);
        const text = await response.text();
        
        // Надежное извлечение чистого JSON
        const jsonStart = text.indexOf('{');
        const jsonEnd = text.lastIndexOf('}') + 1;
        const json = JSON.parse(text.substring(jsonStart, jsonEnd));
        const rows = json.table.rows;
        
        // Безопасный парсинг строк без риска обрушить скрипт
        products = rows.map((row, index) => {
            const cells = row.c || [];
            return {
                id: cells[0] && cells[0].v !== null ? cells[0].v : index,
                name: cells[1] && cells[1].v !== null ? cells[1].v : 'Без названия',
                price: cells[2] && cells[2].v !== null ? Number(cells[2].v) : 0,
                category: cells[3] && cells[3].v !== null ? cells[3].v : 'items',
                description: cells[4] && cells[4].v !== null ? cells[4].v : '',
                image: cells[5] && cells[5].v !== null ? cells[5].v : 'placeholder.jpg'
            };
        });
        
        render();
        } catch (e) {
        const container = document.getElementById('products');
        if (container) {
            container.innerHTML = `<div style="color:red; padding:20px; font-family:sans-serif;">
                <h3>Внимание, ошибка кода:</h3>
                <p>${e.message}</p>
                <p>Стек: ${e.stack ? e.stack.split('\n')[0] : ''}</p>
            </div>`;
        }
}

function render() {
    const container = document.getElementById('products');
    if (!container) return;
    container.innerHTML = '';
    
    let searchTxt = document.getElementById('search').value.toLowerCase();
    let sortBy = document.getElementById('sort').value;

    let filtered = products
        .filter(p => currentCategory === 'all' || p.category === currentCategory)
        .filter(p => p.name.toLowerCase().includes(searchTxt) || p.description.toLowerCase().includes(searchTxt));

    if (sortBy === 'low') filtered.sort((a,b) => a.price - b.price);
    if (sortBy === 'high') filtered.sort((a,b) => b.price - a.price);

    filtered.forEach(p => {
        const imagesArray = p.image.toString().split(',').map(img => img.trim());
        let imagesHtml = '';
        
        if (imagesArray.length > 1) {
            imagesHtml = '<div class="product-gallery">';
            imagesArray.forEach(imgName => {
                imagesHtml += '<img src="images/' + imgName + '" class="gallery-img">';
            });
            imagesHtml += '</div>';
        } else {
            imagesHtml = '<img src="images/' + imagesArray[0] + '" class="main-img">';
        }

        container.innerHTML += `
            <div class="product-card">
                ${imagesHtml}
                <h4>${p.name}</h4>
                <p style="font-size:11px; opacity:0.8; flex-grow:1;">${p.description}</p>
                <p style="margin:5px 0;"><b>${p.price} ₽</b></p>
                <button onclick="addToCart(${p.id})">В корзину</button>
            </div>
        `;
    });
}

document.getElementById('search').addEventListener('input', render);
document.getElementById('sort').addEventListener('change', render);

function filterCategory(cat) {
    currentCategory = cat;
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }
    render();
}

function addToCart(id) {
    let prod = products.find(p => p.id == id);
    if (!prod) return;
    let inCart = cart.find(item => item.id == id);
    if (inCart) { inCart.count++; } else { cart.push({...prod, count: 1}); }
    updateCartButton();
}

function updateCartButton() {
    let count = cart.reduce((sum, item) => sum + item.count, 0);
    document.getElementById('cart-count').innerText = count;
}

function toggleCart() {
    let modal = document.getElementById('cart-modal');
    modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
    let itemsDiv = document.getElementById('cart-items');
    itemsDiv.innerHTML = '';
    let total = 0;
    
    cart.forEach(item => {
        total += item.price * item.count;
        itemsDiv.innerHTML += '<p><b>' + item.name + '</b> x' + item.count + ' — ' + (item.price * item.count) + ' ₽</p>';
    });
    document.getElementById('cart-total').innerText = total;
}

function sendOrder() {
    if (cart.length === 0) return;
    let total = cart.reduce((sum, item) => sum + item.price * item.count, 0);
    let itemsText = cart.map(item => item.name + ' (x' + item.count + ')').join(', ');
    tg.sendData(JSON.stringify({ items: itemsText, total: total }));
    tg.close();
}

loadProducts();

document.getElementById('search').addEventListener('input', render);
document.getElementById('sort').addEventListener('change', render);

function filterCategory(cat) {
    currentCategory = cat;
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    render();
}

function addToCart(id) {
    let prod = products.find(p => p.id == id);
    let inCart = cart.find(item => item.id == id);
    if (inCart) { inCart.count++; } else { cart.push({...prod, count: 1}); }
    updateCartButton();
}

function updateCartButton() {
    let count = cart.reduce((sum, item) => sum + item.count, 0);
    document.getElementById('cart-count').innerText = count;
}

function toggleCart() {
    let modal = document.getElementById('cart-modal');
    modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
    let itemsDiv = document.getElementById('cart-items');
    itemsDiv.innerHTML = '';
    let total = 0;
    
    cart.forEach(item => {
        total += item.price * item.count;
        itemsDiv.innerHTML += `<p><b>${item.name}</b> x${item.count} — ${item.price * item.count} ₽</p>`;
    });
    document.getElementById('cart-total').innerText = total;
}

function sendOrder() {
    if (cart.length === 0) return;
    let total = cart.reduce((sum, item) => sum + item.price * item.count, 0);
    let itemsText = cart.map(item => `${item.name} (x${item.count})`).join(', ');
    tg.sendData(JSON.stringify({ items: itemsText, total: total }));
    tg.close();
}

loadProducts();
