/* static/admin/js/custom_admin.js */

(function($) {
    $(document).ready(function() {
        // Уникальный ключ для этой страницы
        var storageKey = 'django_admin_state_' + window.location.pathname;

        // --- ФУНКЦИЯ ВОССТАНОВЛЕНИЯ ---
        function restoreState() {
            var savedState = [];
            try {
                savedState = JSON.parse(localStorage.getItem(storageKey)) || [];
            } catch (e) {}

            // Проходим по всем свернутым блокам
            $('fieldset.collapse').each(function(index) {
                // Если индекс этого блока есть в сохраненном массиве (значит он был открыт)
                if (savedState.includes(index)) {
                    // Вариант 1: Просто убираем класс (быстро)
                    $(this).removeClass('collapsed');

                    // Вариант 2: Симулируем клик по ссылке "Показать", если Django её уже создал
                    // Это обновляет текст ссылки на "Скрыть"
                    var toggleLink = $(this).find('a.collapse-toggle');
                    if (toggleLink.length > 0 && toggleLink.text().toLowerCase().indexOf('show') !== -1) {
                         toggleLink.trigger('click');
                    }
                }
            });
        }

        // Запускаем восстановление сразу
        restoreState();

        // И еще раз через 200мс, на случай если скрипты Django отработали с задержкой
        setTimeout(restoreState, 200);


        // --- ФУНКЦИЯ СОХРАНЕНИЯ ---
        // Срабатывает при отправке любой формы на странице (в т.ч. "Сохранить и продолжить")
        $('form').on('submit', function() {
            var openFieldsets = [];

            $('fieldset.collapse').each(function(index) {
                // Если у блока НЕТ класса collapsed, значит он открыт. Запоминаем его индекс.
                if (!$(this).hasClass('collapsed')) {
                    openFieldsets.push(index);
                }
            });

            localStorage.setItem(storageKey, JSON.stringify(openFieldsets));
        });

        // Также сохраняем при клике на вкладку (для удобства, если ушли со страницы без сохранения)
        $('fieldset.collapse h2').on('click', function() {
             setTimeout(function(){
                var openFieldsets = [];
                $('fieldset.collapse').each(function(index) {
                    if (!$(this).hasClass('collapsed')) {
                        openFieldsets.push(index);
                    }
                });
                localStorage.setItem(storageKey, JSON.stringify(openFieldsets));
             }, 300);
        });

    });
})(django.jQuery);