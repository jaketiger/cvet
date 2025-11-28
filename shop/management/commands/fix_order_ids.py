# shop/management/commands/fix_order_ids.py

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from orders.models import Order, OrderItem
from shop.models import SiteSettings


class Command(BaseCommand):
    help = 'Перенумеровывает существующие заказы согласно Магическому числу'

    def add_arguments(self, parser):
        # Добавляем флаг --force для запуска без вопросов (для админки)
        parser.add_argument(
            '--force',
            action='store_true',
            help='Запустить без подтверждения (для кнопок в админке)',
        )

    def handle(self, *args, **options):
        # 1. Получаем магическое число
        try:
            start_num = SiteSettings.get_solo().order_start_number
        except:
            self.stdout.write(self.style.ERROR('Сначала сохраните Настройки сайта!'))
            return

        # Получаем заказы, у которых номер меньше магического
        orders_to_fix = Order.objects.filter(id__lt=start_num).order_by('created')

        count = orders_to_fix.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f'Нет заказов с номером меньше {start_num}. Всё ок.'))
            return

        self.stdout.write(f'Найдено {count} заказов для обновления нумерации...')

        # Если НЕ передан флаг --force, спрашиваем подтверждение
        if not options['force']:
            if input("Это изменит номера существующих заказов. Продолжить? (y/n): ") != 'y':
                return

        # Начинаем процесс
        with transaction.atomic():
            for old_order in orders_to_fix:
                old_id = old_order.id

                # 1. Сбрасываем ID, чтобы Django создал новый объект
                old_order.id = None
                # Метод save() в models.py сам подхватит start_num или следующий свободный
                old_order.save()

                new_id = old_order.id

                # 2. Переносим товары из старого заказа в новый
                OrderItem.objects.filter(order_id=old_id).update(order_id=new_id)

                # 3. Удаляем старый заказ-дубликат
                Order.objects.filter(id=old_id).delete()

                self.stdout.write(f'Заказ #{old_id} -> стал #{new_id}')

        # 4. Обновляем счетчик базы данных (PostgreSQL)
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT setval(pg_get_serial_sequence('orders_order', 'id'), (SELECT MAX(id) FROM orders_order));")

        self.stdout.write(self.style.SUCCESS('Готово! Все заказы перенумерованы.'))