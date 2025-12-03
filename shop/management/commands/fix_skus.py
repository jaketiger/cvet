# shop/management/commands/fix_skus.py

from django.core.management.base import BaseCommand
from shop.models import Product, SiteSettings

class Command(BaseCommand):
    help = 'Переписывает артикулы ВСЕМ товарам.'

    def handle(self, *args, **options):
        try:
            start_num = SiteSettings.get_solo().sku_start_number
        except:
            start_num = 11287

        products = Product.objects.all().order_by('id')
        count = products.count()

        if count == 0:
            self.stdout.write("Нет товаров.")
            return

        self.stdout.write("Сброс текущих артикулов...")
        # Сначала обнуляем, чтобы избежать конфликтов уникальности
        Product.objects.all().update(sku=None)

        current = start_num
        for p in products:
            p.sku = str(current)
            p.save()
            current += 1

        self.stdout.write(f"Готово! Артикулы обновлены с {start_num}.")