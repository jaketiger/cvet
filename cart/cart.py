# cart/cart.py

from decimal import Decimal
from django.conf import settings
from shop.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False, postcard_text=None):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'postcard_text': ''
            }

        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        if postcard_text is not None:
            self.cart[product_id]['postcard_text'] = postcard_text

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Перебор товаров в корзине и получение товаров из базы данных.
        """
        product_ids = self.cart.keys()
        # Получаем товары из БД
        products = Product.objects.filter(id__in=product_ids)

        # Создаем словарь для быстрого поиска: {id: product_obj}
        product_map = {str(p.id): p for p in products}

        # Копируем корзину, чтобы не менять сессию напрямую
        cart = self.cart.copy()

        keys_to_remove = []

        for item_id, item in cart.items():
            product = product_map.get(item_id)

            # Если товар удален из базы, помечаем на удаление из корзины
            if not product:
                keys_to_remove.append(item_id)
                continue

            # ВАЖНО: Создаем КОПИЮ элемента, чтобы не засорять сессию объектом Product
            current_item = item.copy()
            current_item['product'] = product
            current_item['price'] = Decimal(item['price'])
            current_item['total_price'] = current_item['price'] * current_item['quantity']

            yield current_item

        # Чистим корзину от удаленных товаров
        if keys_to_remove:
            for item_id in keys_to_remove:
                del self.cart[item_id]
            self.save()

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()