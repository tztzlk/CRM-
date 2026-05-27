(function () {
    'use strict';

    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split('; ') : [];
        for (const c of cookies) {
            const [k, v] = c.split('=');
            if (k === name) return decodeURIComponent(v);
        }
        return '';
    }

    function notify(text, type) {
        const el = document.createElement('div');
        el.className = 'alert alert-' + (type || 'success')
            + ' position-fixed top-0 end-0 m-3 shadow';
        el.style.zIndex = '2000';
        el.textContent = text;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2500);
    }

    function updateColumnTotals() {
        document.querySelectorAll('.board-column').forEach(col => {
            const count = col.querySelectorAll('.deal-card').length;
            let sum = 0;
            col.querySelectorAll('.deal-card').forEach(card => {
                sum += parseFloat(card.dataset.amount || '0');
            });
            const ctr = col.querySelector('.column-count');
            if (ctr) ctr.textContent = count;
            const tot = col.querySelector('.column-total');
            if (tot) tot.textContent = sum.toLocaleString('ru-RU', { maximumFractionDigits: 0 });
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        const csrf = getCookie('csrftoken');
        document.querySelectorAll('.column-body').forEach(body => {
            new Sortable(body, {
                group: 'deals',
                animation: 150,
                ghostClass: 'sortable-ghost',
                dragClass: 'sortable-drag',
                onEnd: function (evt) {
                    const card = evt.item;
                    const dealId = card.dataset.dealId;
                    const targetCol = evt.to.closest('.board-column');
                    const stageId = targetCol.dataset.stageId;
                    if (evt.from === evt.to) { updateColumnTotals(); return; }

                    fetch(`/deals/${dealId}/move/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrf,
                            'X-Requested-With': 'XMLHttpRequest',
                        },
                        body: JSON.stringify({ stage_id: stageId }),
                    })
                    .then(r => r.json().then(d => ({ ok: r.ok, d })))
                    .then(({ ok, d }) => {
                        if (!ok || !d.ok) throw new Error(d.error || 'Ошибка');
                        notify('Сделка перемещена', 'success');
                        const badge = card.querySelector('.status-badge');
                        if (badge) badge.dataset.status = d.status;
                        updateColumnTotals();
                    })
                    .catch(err => {
                        notify('Не удалось переместить: ' + err.message, 'danger');
                        evt.from.insertBefore(card, evt.from.children[evt.oldIndex] || null);
                        updateColumnTotals();
                    });
                },
            });
        });
        updateColumnTotals();
    });
})();
