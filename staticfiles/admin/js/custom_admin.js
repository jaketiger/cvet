// static/admin/js/custom_admin.js

// Убедимся, что jQuery, который использует админка, загружен
if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
    (function($) {
        $(document).ready(function() {

            // --- ЛОГИКА ДЛЯ КНОПКИ "ОЧИСТИТЬ" У ЦВЕТА ---
            $('.clear-color-btn').on('click', function(e) {
                e.preventDefault();
                // Находим соседнее поле цвета и очищаем его значение
                $(this).prev('input[type="color"]').val('');
            });

            // --- ЛОГИКА ДЛЯ ПОЛЗУНКОВ (СЛАЙДЕРОВ) ---
            $('input[type="range"]').each(function() {
                var slider = $(this);
                // Создаем элемент для отображения значения
                var valueDisplay = $('<span class="range-value"></span>').text(slider.val());
                // Вставляем его после слайдера
                slider.after(valueDisplay);

                // Обновляем значение при движении ползунка
                slider.on('input', function() {
                    valueDisplay.text($(this).val());
                });
            });

            // Добавляем немного стилей для красоты
            $('<style>')
                .prop('type', 'text/css')
                .html(`
                    .form-row .range-value {
                        margin-left: 10px;
                        font-weight: bold;
                        font-size: 1.1em;
                        color: #555;
                        min-width: 30px; /* Чтобы цифры не прыгали */
                        display: inline-block;
                    }
                `)
                .appendTo('head');
        });
    })(django.jQuery);
}