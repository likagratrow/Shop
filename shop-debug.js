/*
 * shop-debug.js — постоянный диагностический модуль скорости магазина.
 *
 * По умолчанию полностью молчит и ничего не показывает.
 *
 * На компьютере, когда Mini App открыт в Telegram Desktop:
 *   Ctrl + Alt + Shift + D
 *       — открыть/скрыть панель диагностики.
 *
 * Также доступны из JS-консоли:
 *   shopDebug.open()
 *   shopDebug.close()
 *   shopDebug.toggle()
 *   shopDebug.copy()
 *
 * Модуль должен подключаться ПЕРЕД app.js, чтобы он успевал принять
 * все диагностические отметки загрузки.
 */

(() => {
    const startedAt = performance.now();
    const marks = new Map();
    const values = new Map();

    let panel = null;
    let refreshTimer = null;
    let imageWatchStarted = false;
    let firstImageFinished = false;
    let imageFinished = 0;
    let imageTotal = 0;
    let firstImageAt = null;
    let lastImageAt = null;
    let initialPaintAt = null;

    function elapsed() {
        return performance.now() - startedAt;
    }

    function mark(name, detail = '') {
        const time = elapsed();
        marks.set(name, {time, detail});

        if (panel) {
            renderPanel();
        }
    }

    function setValue(name, value) {
        values.set(name, value);
        if (panel) {
            renderPanel();
        }
    }

    function getTime(name) {
        return marks.get(name)?.time ?? null;
    }

    function formatSeconds(ms) {
        if (ms === null || ms === undefined) return '—';
        if (ms < 1000) return `${Math.round(ms)} ms`;
        return `${(ms / 1000).toFixed(2)} c`;
    }

    function duration(startName, endName) {
        const start = getTime(startName);
        const end = getTime(endName);
        return start === null || end === null ? null : end - start;
    }

    function addRow(lines, label, value) {
        if (value !== null && value !== undefined) {
            lines.push(`<div class="row"><span>${escapeHtml(label)}</span><b>${escapeHtml(formatSeconds(value))}</b></div>`);
        }
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function buildSummaryText() {
        const lines = [
            'SHOP PERFORMANCE',
            '=============================='
        ];

        const rows = [
            ['DOM готов', getTime('dom-ready')],
            ['Access API', duration('access:start', 'access:end')],
            ['  запрос Access API', duration('access:request:start', 'access:response')],
            ['  разбор Access API', duration('access:response', 'access:parsed')],
            ['Google Sheets', duration('sheets:request:start', 'sheets:parsed')],
            ['  ожидание Sheets', duration('sheets:request:start', 'sheets:response')],
            ['  получение текста', duration('sheets:response', 'sheets:text')],
            ['  разбор GViz', duration('sheets:text', 'sheets:parsed')],
            ['Обработка товаров', duration('sheets:parsed', 'products:mapped')],
            ['Render', duration('render:start', 'render:done')],
            ['До первой отрисовки', getTime('catalog:painted')],
            ['1-я картинка', firstImageAt],
            ['Все картинки', lastImageAt],
            ['Картинки: от первой до последней', firstImageAt !== null && lastImageAt !== null ? lastImageAt - firstImageAt : null],
            ['ОТКРЫТИЕ → КАРТОЧКИ', getTime('catalog:painted')],
        ];

        for (const [label, value] of rows) {
            if (value !== null && value !== undefined) {
                lines.push(`${label.padEnd(30, ' ')} ${formatSeconds(value)}`);
            }
        }

        lines.push('------------------------------');
        lines.push(`Товаров: ${values.get('products-count') ?? '—'}`);
        lines.push(`Картинок в первом render: ${imageTotal || '—'}`);

        if (marks.has('products:error')) {
            lines.push(`ОШИБКА: ${marks.get('products:error').detail || 'неизвестно'}`);
        }

        return lines.join('\\n');
    }

    function renderPanel() {
        if (!panel) return;

        const state = document.getElementById('shop-debug-shadow');
        const root = state?.shadowRoot;
        if (!root) return;

        const rows = [];
        addRow(rows, 'До DOM ready', getTime('dom-ready'));
        addRow(rows, 'Access API', duration('access:start', 'access:end'));
        addRow(rows, '↳ запрос', duration('access:request:start', 'access:response'));
        addRow(rows, '↳ разбор', duration('access:response', 'access:parsed'));
        addRow(rows, 'Google Sheets', duration('sheets:request:start', 'sheets:parsed'));
        addRow(rows, '↳ ожидание ответа', duration('sheets:request:start', 'sheets:response'));
        addRow(rows, '↳ получение текста', duration('sheets:response', 'sheets:text'));
        addRow(rows, '↳ разбор GViz', duration('sheets:text', 'sheets:parsed'));
        addRow(rows, 'Обработка товаров', duration('sheets:parsed', 'products:mapped'));
        addRow(rows, 'Render', duration('render:start', 'render:done'));
        addRow(rows, 'До фактической отрисовки', getTime('catalog:painted'));
        addRow(rows, '1-я картинка', firstImageAt);
        addRow(rows, 'Последняя картинка', lastImageAt);
        addRow(rows, 'Картинки: первая → последняя',
            firstImageAt !== null && lastImageAt !== null ? lastImageAt - firstImageAt : null);

        const status = lastImageAt !== null
            ? 'загрузка каталога завершена'
            : imageWatchStarted
                ? `картинки: ${imageFinished}/${imageTotal}`
                : 'идёт загрузка';

        const productCount = values.get('products-count');

        root.getElementById('content').innerHTML = `
            <div class="title">SHOP DEBUG</div>
            <div class="status">${escapeHtml(status)}</div>
            <div class="rows">${rows.join('')}</div>
            <div class="meta">${productCount !== undefined ? `Товаров: ${escapeHtml(productCount)}` : ''}</div>
            <div class="actions">
                <button id="copy">Скопировать</button>
                <button id="hide">Скрыть</button>
            </div>
        `;

        root.getElementById('copy').onclick = async () => {
            try {
                await navigator.clipboard.writeText(buildSummaryText());
                root.getElementById('copy').textContent = 'Скопировано ✓';
                setTimeout(() => {
                    if (root.getElementById('copy')) {
                        root.getElementById('copy').textContent = 'Скопировать';
                    }
                }, 1200);
            } catch {
                window.prompt('Скопируй диагностику:', buildSummaryText());
            }
        };

        root.getElementById('hide').onclick = close;
    }

    function createPanel() {
        if (panel) return panel;

        panel = document.createElement('div');
        panel.id = 'shop-debug-shadow';
        document.body.appendChild(panel);

        const root = panel.attachShadow({mode: 'open'});
        root.innerHTML = `
            <style>
                :host {
                    all: initial;
                }

                .panel {
                    position: fixed;
                    z-index: 2147483647;
                    top: 12px;
                    right: 12px;
                    width: min(360px, calc(100vw - 24px));
                    box-sizing: border-box;
                    padding: 14px;
                    border: 1px solid rgba(255,255,255,.18);
                    border-radius: 14px;
                    background: rgba(20,20,20,.96);
                    color: #fff;
                    font: 14px/1.4 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    box-shadow: 0 10px 40px rgba(0,0,0,.35);
                    backdrop-filter: blur(8px);
                }

                .title {
                    font-weight: 800;
                    font-size: 16px;
                    margin-bottom: 2px;
                }

                .status {
                    opacity: .72;
                    margin-bottom: 10px;
                }

                .rows {
                    display: grid;
                    gap: 5px;
                }

                .row {
                    display: flex;
                    justify-content: space-between;
                    gap: 12px;
                }

                .row span {
                    opacity: .82;
                }

                .row b {
                    white-space: nowrap;
                }

                .meta {
                    margin-top: 10px;
                    opacity: .7;
                }

                .actions {
                    display: flex;
                    gap: 8px;
                    margin-top: 12px;
                }

                button {
                    border: 0;
                    border-radius: 9px;
                    padding: 8px 10px;
                    cursor: pointer;
                    font: inherit;
                }
            </style>

            <div class="panel">
                <div id="content"></div>
            </div>
        `;

        renderPanel();
        return panel;
    }

    function open() {
        createPanel();

        if (!refreshTimer) {
            refreshTimer = setInterval(renderPanel, 200);
        }

        renderPanel();
    }

    function close() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }

        panel?.remove();
        panel = null;
    }

    function toggle() {
        panel ? close() : open();
    }

    function markCatalogPaint() {
        if (getTime('catalog:painted') !== null) return;

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                if (getTime('catalog:painted') === null) {
                    initialPaintAt = elapsed();
                    mark('catalog:painted');
                }
            });
        });
    }

    function watchCatalogImages(container) {
        if (imageWatchStarted) return;
        imageWatchStarted = true;

        const images = Array.from(container.querySelectorAll('img'));
        imageTotal = images.length;
        setValue('images-count', imageTotal);

        if (!images.length) {
            mark('images:none');
            return;
        }

        const finishImage = () => {
            imageFinished += 1;
            const now = elapsed();

            if (!firstImageFinished) {
                firstImageFinished = true;
                firstImageAt = now;
                mark('images:first');
            }

            if (imageFinished >= imageTotal) {
                lastImageAt = now;
                mark('images:all');
            }
        };

        for (const image of images) {
            if (image.complete) {
                finishImage();
            } else {
                image.addEventListener('load', finishImage, {once: true});
                image.addEventListener('error', finishImage, {once: true});
            }
        }

        setValue('images-count', imageTotal);
    }

    function onKeydown(event) {
        if (event.ctrlKey && event.altKey && event.shiftKey && event.key.toLowerCase() === 'd') {
            event.preventDefault();
            toggle();
        }
    }

    mark('debug:loaded');
    document.addEventListener('keydown', onKeydown);

    window.shopDebug = Object.freeze({
        mark,
        setValue,
        watchCatalogImages,
        markCatalogPaint,
        open,
        close,
        toggle,
        copy: async () => {
            await navigator.clipboard.writeText(buildSummaryText());
        },
        summary: buildSummaryText
    });
})();
