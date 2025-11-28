// static/shop/js/admin_scripts.js

function runSkuScript() {
    // 1. Находим поле ввода
    var input = document.getElementById('id_sku_start_number');
    var val = input.value;

    // 2. Добавлено ПОДТВЕРЖДЕНИЕ, как вы просили
    if (confirm('Вы уверены, что хотите пересчитать артикулы всех товаров, начиная с ' + val + '? \n\nЭто действие нельзя отменить.')) {
        // 3. Переход
        window.location.href = 'run-fix-skus/?val=' + val;
    }
}

function runOrderScript() {
    var input = document.getElementById('id_order_start_number');
    var val = input.value;

    if (confirm('Вы уверены? Это изменит номера ВСЕХ существующих заказов.\n\nОни будут пересчитаны, начиная с ' + val + '.\nНажмите ОК для продолжения.')) {
        window.location.href = 'run-fix-orders/?val=' + val;
    }
}