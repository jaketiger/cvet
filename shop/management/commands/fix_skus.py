# shop/management/commands/fix_skus.py

from django.core.management.base import BaseCommand
from shop.models import Product


class Command(BaseCommand):
    help = 'Генерирует артикулы для товаров, у которых их нет (согласно настройкам)'

    def handle(self, *args, **kwargs):
        # Ищем товары без артикула или с пустым артикулом
        products = Product.objects.filter(sku__isnull=True) | Product.objects.filter(sku='')
        count = products.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('Все товары уже имеют артикулы.'))
            return

        self.stdout.write(f'Найдено {count} товаров без артикула. Обработка...')

        for product in products:
            # Просто сохраняем товар.
            # Метод save() в models.py сам найдет последний артикул или start_num и добавит +1
            product.save()
            self.stdout.write(f'Товар "{product.name}" получил артикул {product.sku}')

        self.stdout.write(self.style.SUCCESS('Готово! Всем товарам присвоены артикулы.'))