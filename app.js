const SHEET_ID = '1FcetqNVvXNI78h0mcQdEJBEVXzkHcgaddFrCn2VOugk';

// Берём только A:I.
// J:M — это картинки для просмотра внутри Google Таблиц,
// сайту они не нужны.
const SHEET_URL =
    `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json`;

const tg = window.Telegram?.WebApp;

if (tg) {
    tg.expand();
}


let products = [];
let cart = [];
let currentCategory = 'all';


// ==================================================
// ОБЩИЕ ФУНКЦИИ
// ==================================================

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}


function formatPrice(value) {
    return new Intl.NumberFormat('ru-RU')
        .format(Number(value) || 0);
}


function parseGvizResponse(text) {

    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');

    if (
        start === -1 ||
        end === -1 ||
        end <= start
    ) {
        throw new Error(
            'Google Таблица не вернула данные. Проверьте публикацию таблицы в интернете.'
        );
    }

    try {

        return JSON.parse(
            text.slice(start, end + 1)
        );

    } catch {

        throw new Error(
            'Не удалось разобрать ответ Google Таблицы.'
        );
    }
}


// ==================================================
// ФОТОГРАФИИ
// ==================================================

function getImageUrl(image) {

    const value = String(image || '').trim();

    // Пустая ячейка
    if (!value) {
        return 'images/placeholder.jpg';
    }

    // Старый тип значения Google Sheets.
    // Если в F:I случайно осталась картинка вместо URL —
    // не пытаемся сделать из слова "image" путь.
    if (value.toLowerCase() === 'image') {
        return 'images/placeholder.jpg';
    }

    // Уже готовая ссылка
    if (
        /^(https?:)?\/\//i.test(value) ||
        value.startsWith('data:')
    ) {
        return value;
    }

    // Старый вариант с локальными файлами
    return `images/${encodeURIComponent(value)}`;
}


function getProductImages(product) {

    return [
        product.image,
        product.image2,
        product.image3,
        product.image4
    ]
        .map(value => String(value || '').trim())
        .filter(value => {
            if (!value) return false;

            // Google Sheets иногда отдаёт тип картинки как "image".
            if (value.toLowerCase() === 'image') {
                return false;
            }

            return true;
        });
}


// ==================================================
// ОШИБКА ЗАГРУЗКИ
// ==================================================

function showLoadError(error) {

    const container =
        document.getElementById('products');

    if (!container) return;

    const message =
        error?.message ||
        String(error) ||
        'Неизвестная ошибка';

    container.innerHTML = `
        <div class="load-error">
            <h3>Не удалось загрузить товары</h3>
            <p>${escapeHtml(message)}</p>

            <button
                type="button"
                onclick="loadProducts()"
            >
                Повторить
            </button>
        </div>
    `;
}


// ==================================================
// ЗАГРУЗКА ТОВАРОВ
// ==================================================

async function loadProducts() {

    const container =
        document.getElementById('products');

    if (container) {

        container.innerHTML =
            '<div class="loading">Загрузка товаров...</div>';
    }


    try {

        const response =
            await fetch(SHEET_URL, {
                method: 'GET',
                cache: 'no-store'
            });


        if (!response.ok) {

            throw new Error(
                `Google Sheets вернул HTTP ${response.status}`
            );
        }


        const text =
            await response.text();


        const json =
            parseGvizResponse(text);


        if (
            !json.table ||
            !Array.isArray(json.table.rows)
        ) {

            throw new Error(
                'В ответе Google Таблицы отсутствуют строки с товарами.'
            );
        }


        products =
            json.table.rows
                .map((row, index) => {

                    const cells =
                        row.c || [];


                    const value =
                        (columnIndex, fallback = '') => {

                            const cell =
                                cells[columnIndex];

                            if (
                                cell &&
                                cell.v !== null &&
                                cell.v !== undefined
                            ) {
                                return cell.v;
                            }

                            return fallback;
                        };


                    return {

                        id:
                            value(0, index),

                        name:
                            String(
                                value(1, 'Без названия')
                            ),

                        price:
                            Number(
                                value(2, 0)
                            ) || 0,

                        category:
                            String(
                                value(3, 'items')
                            )
                                .trim()
                                .toLowerCase(),

                        description:
                            String(
                                value(4, '')
                            ),

                        // F
                        image:
                            String(
                                value(5, '')
                            ).trim(),

                        // G
                        image2:
                            String(
                                value(6, '')
                            ).trim(),

                        // H
                        image3:
                            String(
                                value(7, '')
                            ).trim(),

                        // I
                        image4:
                            String(
                                value(8, '')
                            ).trim()
                    };
                });


        console.log(
            'Товары загружены:',
            products
        );


        render();


    } catch (error) {

        console.error(
            'Ошибка загрузки товаров:',
            error
        );

        showLoadError(error);
    }
}


// ==================================================
// ОТРИСОВКА ТОВАРОВ
// ==================================================

function render() {

    const container =
        document.getElementById('products');

    if (!container) return;


    const searchEl =
        document.getElementById('search');

    const sortEl =
        document.getElementById('sort');


    const searchTxt =
        (searchEl?.value || '')
            .trim()
            .toLowerCase();


    const sortBy =
        sortEl?.value || 'default';


    let filtered =
        products
            .filter(product => {

                return (
                    currentCategory === 'all' ||
                    product.category === currentCategory
                );
            })
            .filter(product => {

                return (
                    product.name
                        .toLowerCase()
                        .includes(searchTxt)

                    ||

                    product.description
                        .toLowerCase()
                        .includes(searchTxt)
                );
            });


    if (sortBy === 'low') {

        filtered.sort(
            (a, b) => a.price - b.price
        );
    }


    if (sortBy === 'high') {

        filtered.sort(
            (a, b) => b.price - a.price
        );
    }


    if (!filtered.length) {

        container.innerHTML =
            '<div class="empty-products">Товаров не найдено.</div>';

        return;
    }


    container.innerHTML =
        filtered
            .map(product => {

                const images =
                    getProductImages(product);


                let imagesHtml = '';


                if (images.length > 1) {

                    imagesHtml = `
                        <div class="product-gallery">
                            ${images
                                .map(src => `
                                    <img
                                        src="${escapeHtml(getImageUrl(src))}"
                                        class="gallery-img"
                                        alt="${escapeHtml(product.name)}"
                                        onerror="this.onerror=null; this.src='images/placeholder.jpg';"
                                    >
                                `)
                                .join('')}
                        </div>
                    `;

                } else {

                    const src =
                        images.length
                            ? getImageUrl(images[0])
                            : 'images/placeholder.jpg';


                    imagesHtml = `
                        <img
                            src="${escapeHtml(src)}"
                            class="main-img"
                            alt="${escapeHtml(product.name)}"
                            onerror="this.onerror=null; this.src='images/placeholder.jpg';"
                        >
                    `;
                }


                return `
                    <div
                        class="product-card"
                        onclick="openProductModal(${JSON.stringify(product.id)})"
                    >

                        ${imagesHtml}

                        <h4>
                            ${escapeHtml(product.name)}
                        </h4>

                        <p style="margin:5px 0;">
                            <b>
                                ${formatPrice(product.price)} ₽
                            </b>
                        </p>

                        <button
                            type="button"
                            onclick="event.stopPropagation(); addToCart(${JSON.stringify(product.id)})"
                        >
                            В корзину
                        </button>

                    </div>
                `;
            })
            .join('');
}


// ==================================================
// КАТЕГОРИИ
// ==================================================

function filterCategory(cat, button) {

    currentCategory = cat;


    document
        .querySelectorAll('.cat-btn')
        .forEach(btn => {
            btn.classList.remove('active');
        });


    if (button) {
        button.classList.add('active');
    }


    render();
}


// ==================================================
// КОРЗИНА
// ==================================================

function addToCart(id) {

    const product =
        products.find(
            item =>
                String(item.id) === String(id)
        );


    if (!product) return;


    const inCart =
        cart.find(
            item =>
                String(item.id) === String(id)
        );


    if (inCart) {

        inCart.count++;

    } else {

        cart.push({
            ...product,
            count: 1
        });
    }


    updateCartButton();
}


function updateCartButton() {

    const count =
        cart.reduce(
            (sum, item) =>
                sum + item.count,
            0
        );


    const el =
        document.getElementById('cart-count');


    if (el) {
        el.innerText = count;
    }
}


function toggleCart() {

    const modal =
        document.getElementById('cart-modal');

    if (!modal) return;


    if (modal.style.display === 'block') {

        modal.style.display = 'none';

        return;
    }


    modal.style.display = 'block';

    renderCart();
}


function renderCart() {

    const itemsDiv =
        document.getElementById('cart-items');

    if (!itemsDiv) return;


    let total = 0;


    itemsDiv.innerHTML =
        cart
            .map((item, index) => {

                total +=
                    item.price *
                    item.count;


                return `
                    <div
                        class="cart-item"
                        data-index="${index}"
                        style="margin-bottom:15px;"
                    >

                        <div style="margin-bottom:8px;">
                            <b>
                                ${escapeHtml(item.name)}
                            </b>
                        </div>


                        <div
                            style="
                                display:flex;
                                align-items:center;
                                gap:10px;
                            "
                        >

                            <button
                                type="button"
                                class="cart-minus"
                                data-index="${index}"
                                style="
                                    width:40px;
                                    height:36px;
                                "
                            >
                                −
                            </button>


                            <span
                                style="
                                    min-width:20px;
                                    text-align:center;
                                "
                            >
                                ${item.count}
                            </span>


                            <button
                                type="button"
                                class="cart-plus"
                                data-index="${index}"
                                style="
                                    width:40px;
                                    height:36px;
                                "
                            >
                                +
                            </button>


                            <span style="margin-left:auto;">
                                ${formatPrice(
                                    item.price *
                                    item.count
                                )} ₽
                            </span>


                            <button
                                type="button"
                                class="cart-remove"
                                data-index="${index}"
                                style="
                                    width:40px;
                                    height:36px;
                                "
                            >
                                🗑️
                            </button>

                        </div>

                    </div>
                `;
            })
            .join('');


    const totalEl =
        document.getElementById('cart-total');


    if (totalEl) {

        totalEl.innerText =
            formatPrice(total);
    }


    updateCartButton();


    // ------------------------------
    // МИНУС
    // ------------------------------

    itemsDiv
        .querySelectorAll('.cart-minus')
        .forEach(button => {

            button.addEventListener(
                'click',
                function() {

                    const index =
                        Number(
                            this.dataset.index
                        );


                    if (!cart[index]) return;


                    cart[index].count--;


                    if (
                        cart[index].count <= 0
                    ) {

                        cart.splice(
                            index,
                            1
                        );
                    }


                    renderCart();
                }
            );
        });


    // ------------------------------
    // ПЛЮС
    // ------------------------------

    itemsDiv
        .querySelectorAll('.cart-plus')
        .forEach(button => {

            button.addEventListener(
                'click',
                function() {

                    const index =
                        Number(
                            this.dataset.index
                        );


                    if (!cart[index]) return;


                    cart[index].count++;


                    renderCart();
                }
            );
        });


    // ------------------------------
    // УДАЛЕНИЕ
    // ------------------------------

    itemsDiv
        .querySelectorAll('.cart-remove')
        .forEach(button => {

            button.addEventListener(
                'click',
                function() {

                    const index =
                        Number(
                            this.dataset.index
                        );


                    if (!cart[index]) return;


                    cart.splice(
                        index,
                        1
                    );


                    renderCart();
                }
            );
        });
}


// ==================================================
// МОДАЛЬНАЯ КАРТОЧКА ТОВАРА
// ==================================================

function openProductModal(id) {

    const product =
        products.find(
            item =>
                String(item.id) === String(id)
        );


    if (!product) return;


    const modal =
        document.getElementById('product-modal');


    const content =
        document.getElementById(
            'product-modal-content'
        );


    if (!modal || !content) return;


    const images =
        getProductImages(product);


    const imagesHtml =
        images.length
            ? `
                <div class="product-modal-gallery">

                    ${images
                        .map(src => `
                            <img
                                src="${escapeHtml(getImageUrl(src))}"
                                alt="${escapeHtml(product.name)}"
                                onerror="this.onerror=null; this.src='images/placeholder.jpg';"
                            >
                        `)
                        .join('')}

                </div>
            `
            : '';


    content.innerHTML = `

        ${imagesHtml}


        <h2 class="product-modal-title">
            ${escapeHtml(product.name)}
        </h2>


        <div class="product-modal-description">
            ${escapeHtml(product.description)}
        </div>


        <div class="product-modal-price">
            ${formatPrice(product.price)} ₽
        </div>


        <div class="product-quantity">

            <button
                type="button"
                onclick="changeProductQuantity(-1)"
            >
                −
            </button>


            <span id="product-quantity-value">
                1
            </span>


            <button
                type="button"
                onclick="changeProductQuantity(1)"
            >
                +
            </button>

        </div>


        <button
            type="button"
            class="product-add-btn"
            onclick="addProductToCartFromModal(${JSON.stringify(product.id)})"
        >
            В корзину
        </button>

    `;


    modal.style.display = 'block';
}


function closeProductModal() {

    const modal =
        document.getElementById(
            'product-modal'
        );


    if (modal) {

        modal.style.display = 'none';
    }
}


function changeProductQuantity(delta) {

    const quantityEl =
        document.getElementById(
            'product-quantity-value'
        );


    if (!quantityEl) return;


    let quantity =
        Number(
            quantityEl.innerText
        ) || 1;


    quantity += delta;


    if (quantity < 1) {

        quantity = 1;
    }


    quantityEl.innerText =
        quantity;
}


function addProductToCartFromModal(id) {

    const product =
        products.find(
            item =>
                String(item.id) === String(id)
        );


    if (!product) return;


    const quantityEl =
        document.getElementById(
            'product-quantity-value'
        );


    const quantity =
        Math.max(
            1,
            Number(
                quantityEl?.innerText
            ) || 1
        );


    const inCart =
        cart.find(
            item =>
                String(item.id) === String(id)
        );


    if (inCart) {

        inCart.count += quantity;

    } else {

        cart.push({
            ...product,
            count: quantity
        });
    }


    updateCartButton();

    closeProductModal();
}


// ==================================================
// ОТПРАВКА ЗАКАЗА
// ==================================================

function sendOrder() {

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


    const payload =
        JSON.stringify({
            items: itemsText,
            total: total
        });


    if (tg?.sendData) {

        tg.sendData(payload);

        tg.close();

    } else {

        alert(
            'Заказ можно оформить только внутри Telegram.'
        );
    }
}


// ==================================================
// СТАРТ
// ==================================================

document.addEventListener(
    'DOMContentLoaded',
    () => {

        document
            .getElementById('search')
            ?.addEventListener(
                'input',
                render
            );


        document
            .getElementById('sort')
            ?.addEventListener(
                'change',
                render
            );


        loadProducts();
    }
);
