// ==================================================
// ФИНАЛЬНЫЕ ДОПОЛНЕНИЯ МАГАЗИНА
// Только точечные UX-изменения. Основная логика магазина
// и галерея товаров не переписываются.
// ==================================================

const CATEGORY_SHEET_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=${encodeURIComponent('Категории')}`;
const categoryDescriptions = {};
const originalProductsOrder = [];
let searchCategoryFilter = null;

const enhancementStyle = document.createElement('style');
enhancementStyle.textContent = `
    .categories { position: sticky; top: 0; z-index: 6; padding: 8px 0; background: var(--tg-theme-bg-color, #fff); }
    .category-description { margin: 0 0 15px; padding: 10px 12px; border-radius: 10px; background: var(--tg-theme-secondary-bg-color, #f5f5f5); color: var(--tg-theme-text-color, #000); font-size: 14px; line-height: 1.45; }
    .search-wrap { position: relative; flex: 1; min-width: 0; }
    .search-wrap #search { width: 100%; box-sizing: border-box; padding-right: 36px; }
    .search-clear { position: absolute; top: 50%; right: 8px; width: 28px; height: 28px; transform: translateY(-50%); border: none; background: transparent; color: #888; font-size: 22px; line-height: 28px; padding: 0; cursor: pointer; }
    .search-clear[hidden] { display: none; }
    .search-active { margin: -7px 0 10px; font-size: 12px; color: var(--tg-theme-hint-color, #888); }
    .search-empty-hint { padding: 18px 12px; text-align: center; color: var(--tg-theme-hint-color, #888); font-size: 14px; line-height: 1.45; }
`;
document.head.appendChild(enhancementStyle);

const categoriesEl = document.querySelector('.categories');
if (categoriesEl) {
    const allButton = categoriesEl.querySelector('[onclick*="filterCategory(\'all\'"]');
    if (allButton) allButton.remove();
    const itemsButton = categoriesEl.querySelector('[onclick*="filterCategory(\'items\'"]');
    if (itemsButton) filterCategory('items', itemsButton);
    const description = document.createElement('div');
    description.id = 'category-description';
    description.className = 'category-description';
    categoriesEl.insertAdjacentElement('afterend', description);
}

function updateCategoryDescription(category) {
    const description = document.getElementById('category-description');
    if (!description) return;
    description.innerText = categoryDescriptions[category] || '';
    description.style.display = categoryDescriptions[category] ? '' : 'none';
}

const originalFilterCategory = filterCategory;
filterCategory = function(category, button) {
    const hasSearch = Boolean(document.getElementById('search')?.value.trim());
    if (hasSearch) searchCategoryFilter = category;
    originalFilterCategory(category, button);
    updateCategoryDescription(category);
    updateSearchState();
};

async function loadCategoryDescriptions() {
    try {
        const response = await fetch(CATEGORY_SHEET_URL, { method: 'GET', cache: 'no-store' });
        if (!response.ok) return;
        const text = await response.text();
        const json = parseGvizResponse(text);
        if (!json.table || !Array.isArray(json.table.rows)) return;
        json.table.rows.forEach(row => {
            const cells = row.c || [];
            const category = String(cells[0]?.v ?? '').trim().toLowerCase();
            const description = String(cells[1]?.v ?? '').trim();
            if (category && category !== 'category' && category !== 'категория') categoryDescriptions[category] = description;
        });
        updateCategoryDescription(currentCategory);
    } catch (error) {
        console.warn('Не удалось загрузить описания категорий:', error);
    }
}

// ==================================================
// ПОИСК — КНОПКА ОЧИСТКИ + ПОИСК ПО ВСЕМУ КАТАЛОГУ
// ==================================================

const searchEl = document.getElementById('search');

function updateSearchState() {
    const searchValue = document.getElementById('search')?.value.trim();
    const state = document.getElementById('search-active');
    if (!state) return;
    if (!searchValue) {
        state.style.display = 'none';
        state.innerText = '';
        return;
    }
    state.style.display = '';
    state.innerText = searchCategoryFilter
        ? `Поиск: ${searchValue} · ${getCategoryName(searchCategoryFilter)}`
        : `Поиск по всему каталогу: ${searchValue}`;
}

function getCategoryName(category) {
    const button = document.querySelector(`[onclick*="filterCategory('${category}'"]`);
    return button?.innerText?.trim() || category;
}

if (searchEl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'search-wrap';
    searchEl.parentNode.insertBefore(wrapper, searchEl);
    wrapper.appendChild(searchEl);
    const clearButton = document.createElement('button');
    clearButton.type = 'button';
    clearButton.className = 'search-clear';
    clearButton.innerText = '×';
    clearButton.setAttribute('aria-label', 'Очистить поиск');
    clearButton.hidden = !searchEl.value;
    clearButton.addEventListener('click', () => {
        searchEl.value = '';
        searchCategoryFilter = null;
        clearButton.hidden = true;
        render();
        updateSearchState();
        searchEl.focus();
    });
    wrapper.appendChild(clearButton);
    const searchState = document.createElement('div');
    searchState.id = 'search-active';
    searchState.className = 'search-active';
    searchState.style.display = 'none';
    wrapper.insertAdjacentElement('afterend', searchState);
    searchEl.addEventListener('input', () => {
        clearButton.hidden = !searchEl.value;
        searchCategoryFilter = null;
        render();
        updateSearchState();
    });
}

// ==================================================
// Поиск: без текста — выбранная категория.
// С текстом — весь каталог.
// После нажатия категории во время поиска —
// поиск остаётся, а категория становится вторым фильтром.
// ==================================================

const originalRender = render;
render = function() {
    const searchValue = document.getElementById('search')?.value.trim();
    if (searchValue) {
        const savedCategory = currentCategory;
        currentCategory = searchCategoryFilter || 'all';
        originalRender();
        currentCategory = savedCategory;
        updateSearchState();
        const productContainer = document.querySelector('.products');
        if (productContainer && !productContainer.children.length) {
            productContainer.innerHTML = `
                <div class="search-empty-hint">
                    В этой категории ничего не найдено.<br>
                    Сбросьте поиск или выберите другую категорию.
                </div>
            `;
        }
        return;
    }
    searchCategoryFilter = null;
    originalRender();
    updateSearchState();
};

const sortEl = document.getElementById('sort');
if (sortEl) {
    const azOption = document.createElement('option');
    azOption.value = 'az';
    azOption.innerText = 'А–Я';
    sortEl.appendChild(azOption);
    sortEl.addEventListener('change', () => {
        if (sortEl.value === 'az') {
            products.sort((a, b) => a.name.localeCompare(b.name, 'ru', { sensitivity: 'base' }));
        } else {
            products.splice(0, products.length, ...originalProductsOrder);
        }
        render();
    });
}

const originalLoadProducts = loadProducts;
loadProducts = async function() {
    await originalLoadProducts();
    originalProductsOrder.splice(0, originalProductsOrder.length, ...products);
};

const productModal = document.getElementById('product-modal');
if (productModal) {
    productModal.addEventListener('click', event => {
        if (event.target === productModal) closeProductModal();
    });
}

const originalChangeProductQuantity = changeProductQuantity;
changeProductQuantity = function(id, delta) {
    originalChangeProductQuantity(id, delta);
    const button = document.querySelector('.product-add-btn');
    if (button) button.innerText = 'В корзину';
};

const originalAddProductToCartFromModal = addProductToCartFromModal;
addProductToCartFromModal = function(id) {
    originalAddProductToCartFromModal(id);
    const button = document.querySelector('.product-add-btn');
    if (button) button.innerText = 'В корзину';
};

loadCategoryDescriptions();
