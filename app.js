const SHEET_ID = `1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk`; 
const SHEET_URL = `https://google.com{SHEET_ID}/gviz/tq?tqx=out:json`;

let tg = window.Telegram.WebApp;
tg.expand();

let products = [];
let cart = [];
let currentCategory = 'all';

async function loadProducts() {
    try {
        const response = await fetch(SHEET_URL);
        const text = await response.text();
        const json = JSON.parse(text.substr(47).slice(0, -2));
        const rows = json.table.rows;
        
        products = rows.map((row, index) => ({
            id: row.c[0] ? row.c[0].v : index,
            name: row.c[1] ? row.c[1].v : '',
            price: row.c[2] ? Number(row.c[2].v) : 0,
            category: row.c[3] ? row.c[3].v : 'items',
            description: row.c[4] ? row.c[4].v : '',
            image: row.c[5] ? row.c[5].v : 'placeholder.jpg'
        }));
        render();
    } catch (e) {
        document.getElementById('products').innerText = 'Ошибка чтения таблицы.';
    }
}

function render() {
    const container = document.getElementById('products');
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
            imagesHtml = `<div class="product-gallery">`;
            imagesArray.forEach(imgName => {
                imagesHtml += `<img src="images/${imgName}" class="gallery-img">`;
            });
            imagesHtml += `</div>`;
        } else {
            imagesHtml = `<img src="images/${imagesArray[0]}" class="main-img">`;
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
