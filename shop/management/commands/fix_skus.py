# shop/management/commands/fix_skus.py

from django.core.management.base import BaseCommand
from shop.models import Product, SiteSettings


class Command(BaseCommand):
    help = 'Переписывает артикулы ВСЕМ товарам, начиная с указанного в настройках числа.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Тихий режим')

    def handle(self, *args, **options):
        try:
            start_num = SiteSettings.get_solo().sku_start_number
        except:
            start_num = 11287

        products = Product.objects.all().order_by('id')
        count = products.count()

        if count == 0:
            self.stdout.write("Нет товаров для обновления.")
            return

        # === ГЛАВНОЕ ИСПРАВЛЕНИЕ ===
        # Сначала сбрасываем артикулы в NULL, чтобы освободить номера
        # и избежать ошибки "уникальное значение уже существует"
        self.stdout.write("Сброс текущих артикулов...")
        Product.objects.all().update(sku=None)
        # ===========================

        updated_count = 0
        current_sku = start_num

        # Проходим по всем товарам и ПРИСВАИВАЕМ новые номера
        for product in products:
            new_sku_str = str(current_sku)

            product.sku = new_sku_str
            product.save()
            updated_count += 1

            current_sku += 1

        self.stdout.write(f"Готово! Обработано товаров: {count}. Нумерация с {start_num}.")