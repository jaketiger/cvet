# shop/management/commands/fix_order_ids.py

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from orders.models import Order, OrderItem
from shop.models import SiteSettings


class Command(BaseCommand):
    help = 'Перенумеровывает ВСЕ заказы. Поддерживает и увеличение, и уменьшение номеров.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Тихий режим')

    def handle(self, *args, **options):
        try:
            start_num = SiteSettings.get_solo().order_start_number
        except:
            self.stdout.write("Нет настроек сайта.")
            return

        # Берем ВСЕ заказы, сортируем по дате создания (чтобы сохранить хронологию)
        # Сортировка по id на случай, если created совпадает
        orders = list(Order.objects.all().order_by('created', 'id'))
        count = len(orders)

        if count == 0:
            self.stdout.write("Нет заказов для обновления.")
            return

        if not options['force']:
            if input(f"Найдено {count} заказов. Перенумеровать их начиная с {start_num}? (y/n): ") != 'y':
                return

        # ВАЖНО: Используем транзакцию, чтобы если что-то упадет, ничего не сломалось
        with transaction.atomic():
            self.stdout.write("Этап 1: Перенос заказов во временный диапазон...")

            # Список для хранения временных ID, чтобы потом их найти
            temp_ids = []

            # ЭТАП 1: Освобождаем номера.
            # Пересоздаем каждый заказ с ID = (старый_ID + 10 000 000)
            for order in orders:
                old_id = order.id
                temp_id = old_id + 10000000

                # Копируем дату создания, так как auto_now_add её перезапишет
                old_created = order.created
                old_updated = order.updated

                # Сбрасываем ID -> Django создаст новый объект
                order.id = temp_id
                order.save()  # Теперь это новый заказ с гигантским ID

                # Восстанавливаем даты (Django их обновил при создании)
                Order.objects.filter(id=temp_id).update(created=old_created, updated=old_updated)

                # Переносим товары из старого заказа в этот временный
                OrderItem.objects.filter(order_id=old_id).update(order_id=temp_id)

                # Удаляем старый заказ (освобождаем номер)
                Order.objects.filter(id=old_id).delete()

                temp_ids.append(temp_id)

            self.stdout.write("Этап 2: Присвоение новых красивых номеров...")

            # ЭТАП 2: Берем временные заказы и даем им правильные номера
            # Сортируем temp_ids, чтобы сохранить порядок
            current_new_id = start_num

            for tmp_id in temp_ids:
                # Получаем временный заказ
                order = Order.objects.get(id=tmp_id)

                old_created = order.created
                old_updated = order.updated

                # Присваиваем целевой ID
                order.id = current_new_id
                order.save()

                # Восстанавливаем даты снова
                Order.objects.filter(id=current_new_id).update(created=old_created, updated=old_updated)

                # Переносим товары из временного в финальный
                OrderItem.objects.filter(order_id=tmp_id).update(order_id=current_new_id)

                # Удаляем временный
                Order.objects.filter(id=tmp_id).delete()

                current_new_id += 1

        # ЭТАП 3: Синхронизация счетчика базы данных (PostgreSQL)
        # Чтобы следующий НОВЫЙ заказ получил правильный номер (max + 1)
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT setval(pg_get_serial_sequence('orders_order', 'id'), (SELECT MAX(id) FROM orders_order));")

        self.stdout.write(f"Успешно! Заказы перенумерованы: {count} шт. (с {start_num} по {current_new_id - 1})")