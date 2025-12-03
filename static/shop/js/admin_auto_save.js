/* static/shop/js/admin_auto_save.js */

document.addEventListener('DOMContentLoaded', function() {

    // URL для отправки (формируем динамически или хардкодим, т.к. это админка)
    const UPDATE_URL = 'ajax/update-status/';

    // Находим все селекты статусов в таблице
    // Обычно в Django admin list_editable поля имеют имена вида form-0-status, form-1-status...
    const statusSelects = document.querySelectorAll('select[name$="-status"]');

    if (statusSelects.length === 0) return;

    // Создаем элемент для уведомлений (Toast)
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 20px; right: 20px;
        background: #333; color: #fff; padding: 12px 24px;
        border-radius: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        z-index: 9999; transform: translateY(100px); transition: transform 0.3s ease;
        font-family: sans-serif; font-size: 14px;
    `;
    document.body.appendChild(toast);

    function showToast(msg, type='success') {
        toast.textContent = msg;
        toast.style.background = type === 'success' ? '#28a745' : '#dc3545';
        toast.style.transform = 'translateY(0)';
        setTimeout(() => {
            toast.style.transform = 'translateY(100px)';
        }, 3000);
    }

    // Добавляем обработчик на каждый селект
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            const row = this.closest('tr');

            // Находим скрытое поле ID в этой же строке (Django хранит его как form-N-id)
            // Имя селекта: form-0-status -> ID будет: form-0-id
            const idInputName = this.name.replace('-status', '-id');
            const idInput = document.querySelector(`input[name="${idInputName}"]`);

            if (!idInput) {
                console.error("Не найден ID заказа для строки");
                return;
            }

            const orderId = idInput.value;
            const newStatus = this.value;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Визуальный эффект загрузки (блеклость)
            this.style.opacity = '0.5';
            this.disabled = true;

            // Отправка запроса
            fetch(UPDATE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    id: orderId,
                    status: newStatus
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(`✔ ${data.message}`, 'success');
                    // Подсветка зеленым на секунду
                    this.style.backgroundColor = '#d4edda';
                    setTimeout(() => this.style.backgroundColor = '', 1000);
                } else {
                    showToast(`Ошибка: ${data.error}`, 'error');
                    this.style.backgroundColor = '#f8d7da';
                }
            })
            .catch(err => {
                showToast('Ошибка сети', 'error');
                console.error(err);
            })
            .finally(() => {
                this.style.opacity = '1';
                this.disabled = false;
            });
        });
    });
});