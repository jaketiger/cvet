# favorites/favorites.py

from django.conf import settings
from shop.models import Product


class Favorites:
    def __init__(self, request):
        self.session = request.session
        favorites = self.session.get(settings.FAVORITES_SESSION_ID)
        if not favorites:
            favorites = self.session[settings.FAVORITES_SESSION_ID] = []
        self.favorites = favorites

    def add(self, product):
        product_id = int(product.id)
        if product_id not in self.favorites:
            self.favorites.append(product_id)
            self.save()

    def remove(self, product):
        product_id = int(product.id)
        if product_id in self.favorites:
            self.favorites.remove(product_id)
            self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        # Получаем товары из БД
        products = Product.objects.filter(id__in=self.favorites)
        for product in products:
            yield product

    def __len__(self):
        return len(self.favorites)

    def has_product(self, product_id):
        return int(product_id) in self.favorites