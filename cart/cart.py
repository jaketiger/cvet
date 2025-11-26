# cart/cart.py

from decimal import Decimal
from django.conf import settings
from shop.models import Product


class Cart:
    def __init__(self, request):
        """
        Инициализируем корзину.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # если корзины нет в сессии, создаем ее
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False, postcard_text=None):
        """
        Добавить товар в корзину или обновить его количество.
        postcard_text: Текст бесплатной открытки (опционально).
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'postcard_text': ''  # Инициализируем поле
            }

        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        # Сохраняем текст открытки, если он был передан
        if postcard_text is not None:
            self.cart[product_id]['postcard_text'] = postcard_text

        self.save()

    def save(self):
        # помечаем сессию как "измененную", чтобы убедиться, что она сохранится
        self.session.modified = True

    def remove(self, product):
        """
        Удаление товара из корзины.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Перебор товаров в корзине и получение товаров из базы данных.
        """
        product_ids = self.cart.keys()
        # получаем объекты товаров и добавляем их в корзину
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        keys_to_remove = []

        for item_id, item in cart.items():
            # Если товар был удален из БД
            if 'product' not in item:
                keys_to_remove.append(item_id)
                continue

            # === ВАЖНОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ ===
            # Мы создаем КОПИЮ словаря для текущего товара.
            # Это нужно, чтобы мы могли добавить туда Decimal (для шаблона),
            # но НЕ загрязняли им основную сессию (которая принимает только JSON).
            current_item = item.copy()

            current_item['price'] = Decimal(item['price'])
            current_item['total_price'] = current_item['price'] * current_item['quantity']

            yield current_item
            # ================================

        # Удаляем мусор (несуществующие товары)
        if keys_to_remove:
            for item_id in keys_to_remove:
                del self.cart[item_id]
            self.save()

    def __len__(self):
        """
        Считаем общее количество товаров в корзине.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Считаем общую стоимость товаров в корзине.
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        # очистка корзины в сессии
        del self.session[settings.CART_SESSION_ID]
        self.save()