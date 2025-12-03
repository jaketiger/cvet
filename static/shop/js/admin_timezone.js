// static/shop/js/admin_timezone.js

document.addEventListener("DOMContentLoaded", function() {
    const select = document.getElementById('id_site_time_zone');
    // Ищем контейнер. В Django Admin readonly поля часто оборачиваются,
    // поэтому ищем наш span по ID
    const clockContainer = document.getElementById('timezone-clock-preview');

    if (!select || !clockContainer) return;

    function updateClock() {
        const selectedTz = select.value;
        if (!selectedTz) return;

        try {
            const now = new Date();
            // Форматируем время под выбранную зону
            const timeString = new Intl.DateTimeFormat('ru-RU', {
                timeZone: selectedTz,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                day: 'numeric',
                month: 'long',
                weekday: 'short'
            }).format(now);

            clockContainer.textContent = "🕒 " + timeString;
            clockContainer.style.color = "#28a745";
            clockContainer.style.fontWeight = "bold";

        } catch (e) {
            clockContainer.textContent = "⚠ Некорректная зона";
        }
    }

    // Запуск
    updateClock();
    select.addEventListener('change', updateClock);
    setInterval(updateClock, 1000);
});