 
// static/admin/js/order_item_admin.js

(function($) {
    $(document).ready(function() {
        $(document).on('change', '.field-product select', function() {
            const productId = $(this).val();
            const priceInput = $(this).closest('tr').find('.field-price input');

            if (productId) {
                $.ajax({
                    url: '/get-product-price/',
                    data: {
                        'product_id': productId
                    },
                    dataType: 'json',
                    success: function(data) {
                        if (data.price) {
                            priceInput.val(data.price.replace(',', '.')); // Заменяем запятую на точку для правильного формата
                        }
                    }
                });
            } else {
                priceInput.val('');
            }
        });
    });
})(django.jQuery);