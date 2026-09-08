// ==================================================
// ФИНАЛЬНЫЕ ДОПОЛНЕНИЯ МАГАЗИНА
// Здесь только изменения UX, не затрагивающие
// основную логику магазина.
// ==================================================

const CATEGORY_SHEET_URL =
    `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=${encodeURIComponent('Категории')}`;

const categoryDescriptions = {};
const originalProductsOrder = [];


// ==================================================
// СТИЛИ
// ==================================================

const enhancementStyle = document.createElement('style');

enhancementStyle.textContent = `
    .categories {
        position: sticky;
        top: 0;
        z-index: 6;
        padding: 8px 0;
        background: var(--tg-theme-bg-color, #fff);
    }

    .category-description {
        margin: 0 0 15px;
        padding: 10px 12px;
        border-radius: 10px;
        background: var(--tg-theme-secondary-bg-color, #f5f5f5);
        color: var(--tg-theme-text-color, #000);
        font-size: 14px;
        line-height: 1.45;
    }

    .search-wrap {
        position: relative;
        flex: 1;
        min-width: 0;
    }

    .search-wrap #search {
        width: 100%;
        box-sizing: border-box;
        padding-right: 36px;
    }

    .search-clear {
        position: absolute;
        top: 50%;
        right: 8px;
        width: 28px;
        height: 28px;
        transform: translateY(-50%);
        border: none;
        background: transparent;
        color: #888;
        font-size: 22px;
        line-height: 28px;
        padding: 0;
        cursor: pointer;
    }

    .search-clear[hidden] {
        display: none;
    }
`;

document.head.appendChild(enhancementStyle);


// ==================================================
// КАТЕГОРИИ
// ==================================================

const categoriesEl =
    document.querySelector('.categories');

if (categoriesEl) {

    const allButton =
        categoriesEl.querySelector(
            '[onclick*="filterCategory(\'all\'"]'
        );

    if (allButton) {
        allButton.remove();
    }

    const itemsButton =
        categoriesEl.querySelector(
            '[onclick*="filterCategory(\'items\'"]'
        );

    if (itemsButton) {
        filterCategory('items', itemsButton);
    }

    const description =
        document.createElement('div');

    description.id =
        'category-description';

    description.className =
        'category-description';

    categoriesEl.insertAdjacentElement(
        'afterend',
        description
    );
}


function updateCategoryDescription(category) {

    const description =
        document.getElementById(
            'category-description'
        );

    if (!description) return;

    description.innerText =
        categoryDescriptions[category] || '';

    description.style.display =
        categoryDescriptions[category]
            ? ''
            : 'none';
}


const originalFilterCategory =
    filterCategory;

filterCategory = function(
    category,
    button
) {

    originalFilterCategory(
        category,
        button
    );

    updateCategoryDescription(category);
};


async function loadCategoryDescriptions() {

    try {

        const response =
            await fetch(
                CATEGORY_SHEET_URL,
                {
                    method: 'GET',
                    cache: 'no-store'
                }
            );

        if (!response.ok) return;

        const text =
            await response.text();

        const json =
            parseGvizResponse(text);

        if (!json.table || !Array.isArray(json.table.rows)) {
            return;
        }

        json.table.rows.forEach(row => {

            const cells = row.c || [];

            const category =
                String(cells[0]?.v ?? '')
                    .trim()
                    .toLowerCase();

            const description =
                String(cells[1]?.v ?? '')
                    .trim();

            if (
                category &&
                category !== 'category' &&
                category !== 'категория'
            ) {
                categoryDescriptions[category] =
                    description;
            }
        });

        updateCategoryDescription(
            currentCategory
        );

    } catch (error) {

        console.warn(
            'Не удалось загрузить описания категорий:',
            error
        );
    }
}


// ==================================================
// ПОИСК — КНОПКА ОЧИСТКИ
// ==================================================

const searchEl =
    document.getElementById('search');

if (searchEl) {

    const wrapper =
        document.createElement('div');

    wrapper.className =
        'search-wrap';

    searchEl.parentNode.insertBefore(
        wrapper,
        searchEl
    );

    wrapper.appendChild(searchEl);

    const clearButton =
        document.createElement('button');

    clearButton.type = 'button';
    clearButton.className = 'search-clear';
    clearButton.innerText = '×';
    clearButton.setAttribute(
        'aria-label',
        'Очистить поиск'
    );

    clearButton.hidden =
        !searchEl.value;

    clearButton.addEventListener(
        'click',
        () => {
            searchEl.value = '';
            clearButton.hidden = true;
            render();
            searchEl.focus();
        }
    );

    wrapper.appendChild(clearButton);

    searchEl.addEventListener(
        'input',
        () => {
            clearButton.hidden =
                !searchEl.value;
        }
    );
}


// ==================================================
// СОРТИРОВКА A–Я
// ==================================================

const sortEl =
    document.getElementById('sort');

if (sortEl) {

    const azOption =
        document.createElement('option');

    azOption.value = 'az';
    azOption.innerText = 'А–Я';

    sortEl.appendChild(azOption);

    originalProductsOrder.push(
        ...products
    );

    sortEl.addEventListener(
        'change',
        () => {

            if (sortEl.value === 'az') {

                products.sort(
                    (a, b) =>
                        a.name.localeCompare(
                            b.name,
                            'ru',
                            {
                                sensitivity: 'base'
                            }
                        )
                );

            } else {

                products.splice(
                    0,
                    products.length,
                    ...originalProductsOrder
                );
            }

            render();
        }
    );
}


// ==================================================
// КАРТОЧКА ТОВАРА — ЗАКРЫТИЕ ПО ФОНУ
// ==================================================

const productModal =
    document.getElementById('product-modal');

if (productModal) {

    productModal.addEventListener(
        'click',
        event => {
            if (event.target === productModal) {
                closeProductModal();
            }
        }
    );
}


// ==================================================
// КНОПКА В МОДАЛЬНОМ ОКНЕ
// ==================================================

const originalChangeProductQuantity =
    changeProductQuantity;

changeProductQuantity = function(
    id,
    delta
) {

    originalChangeProductQuantity(
        id,
        delta
    );

    const button =
        document.querySelector(
            '.product-add-btn'
        );

    if (button) {
        button.innerText =
            'В корзину';
    }
};


const originalAddProductToCartFromModal =
    addProductToCartFromModal;

addProductToCartFromModal = function(id) {

    originalAddProductToCartFromModal(id);

    const button =
        document.querySelector(
            '.product-add-btn'
        );

    if (button) {
        button.innerText =
            'В корзину';
    }
};


loadCategoryDescriptions();
