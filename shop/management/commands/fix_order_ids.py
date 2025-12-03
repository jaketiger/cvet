# shop/management/commands/fix_order_ids.py

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from orders.models import Order
from shop.models import SiteSettings


class Command(BaseCommand):
    help = 'Перенумеровывает заказы, меняя ID напрямую в БД (безопасно).'

    def handle(self, *args, **options):
        try:
            start_num = SiteSettings.get_solo().order_start_number
        except:
            self.stdout.write("Нет настроек.")
            return

        orders = list(Order.objects.all().order_by('created', 'id'))
        if not orders:
            self.stdout.write("Нет заказов.")
            return

        with transaction.atomic():
            with connection.cursor() as cursor:
                # Отключаем проверку ключей на время транзакции (для Postgres)
                try:
                    cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
                except:
                    pass

                    # ЭТАП 1: Сдвигаем все ID в безопасную зону (+10млн), чтобы освободить место
                temp_offset = 10000000
                id_map = {}  # Запоминаем: Старый ID -> Временный ID

                # Обратный порядок не обязателен при сдвиге в пустую зону, но надежнее
                for order in orders:
                    old_id = order.id
                    temp_id = old_id + temp_offset
                    id_map[old_id] = temp_id

                    # 1. Меняем ID в таблице товаров (ссылки на заказ)
                    cursor.execute("UPDATE orders_orderitem SET order_id = %s WHERE order_id = %s", [temp_id, old_id])
                    # 2. Меняем ID самого заказа
                    cursor.execute("UPDATE orders_order SET id = %s WHERE id = %s", [temp_id, old_id])

                # ЭТАП 2: Присваиваем красивые номера
                current_new_id = start_num

                for order in orders:
                    # Ищем, где сейчас лежит этот заказ (во временной зоне)
                    old_id_was = order.id
                    current_temp_id = id_map[old_id_was]

                    # 1. Обновляем товары
                    cursor.execute("UPDATE orders_orderitem SET order_id = %s WHERE order_id = %s",
                                   [current_new_id, current_temp_id])
                    # 2. Обновляем заказ
                    cursor.execute("UPDATE orders_order SET id = %s WHERE id = %s", [current_new_id, current_temp_id])

                    current_new_id += 1

                # ЭТАП 3: Синхронизируем счетчик БД (чтобы новые заказы шли дальше)
                try:
                    cursor.execute(
                        "SELECT setval(pg_get_serial_sequence('orders_order', 'id'), (SELECT MAX(id) FROM orders_order));")
                except:
                    pass

        self.stdout.write(f"Успешно! Заказы перенумерованы начиная с {start_num}.")