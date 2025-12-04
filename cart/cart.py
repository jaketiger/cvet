# cart/cart.py

from decimal import Decimal
from django.conf import settings
from shop.models import Product
from promo.models import PromoCode


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # Получаем ID промокода из сессии
        self.promo_id = self.session.get('promo_id')
        # ДОБАВЛЕНО: Получаем посткарты из сессии
        self.postcards = self.session.get('postcards', {})
        # ДОБАВЛЕНО: Получаем тексты открыток
        self.postcard_texts = self.session.get('postcard_texts', {})

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
            # ДОБАВЛЕНО: Сохраняем текст в сессии
            if 'postcard_texts' not in self.session:
                self.session['postcard_texts'] = {}
            self.session['postcard_texts'][product_id] = postcard_text

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            # Удаляем также связанную открытку если есть
            if product_id in self.postcards:
                del self.postcards[product_id]
                self.session['postcards'] = self.postcards
            # Удаляем текст открытки если есть
            if product_id in self.postcard_texts:
                del self.postcard_texts[product_id]
                self.session['postcard_texts'] = self.postcard_texts
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}

        cart = self.cart.copy()

        keys_to_remove = []

        for item_id, item in cart.items():
            product = product_map.get(item_id)

            if not product:
                keys_to_remove.append(item_id)
                continue

            current_item = item.copy()
            current_item['product'] = product
            current_item['price'] = Decimal(item['price'])
            current_item['total_price'] = current_item['price'] * current_item['quantity']

            # ДОБАВЛЕНО: Добавляем информацию об открытке для этого товара
            current_item['postcard_info'] = self.postcards.get(item_id, {})

            # ДОБАВЛЕНО: Добавляем текст открытки из сессии
            if item_id in self.postcard_texts:
                current_item['postcard_text'] = self.postcard_texts[item_id]

            yield current_item

        if keys_to_remove:
            for item_id in keys_to_remove:
                del self.cart[item_id]
                if item_id in self.postcards:
                    del self.postcards[item_id]
                if item_id in self.postcard_texts:
                    del self.postcard_texts[item_id]
            self.save()

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        # Очищаем не только корзину, но и промокод и открытки
        del self.session[settings.CART_SESSION_ID]
        if 'promo_id' in self.session:
            del self.session['promo_id']
        if 'postcards' in self.session:
            del self.session['postcards']
        if 'postcard_texts' in self.session:
            del self.session['postcard_texts']
        self.save()

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ОТКРЫТКАМИ ===

    def add_postcard_to_product(self, product_id, postcard_id, postcard_price=0, postcard_title=""):
        """Добавляет открытку к конкретному товару"""
        product_id_str = str(product_id)
        if product_id_str not in self.cart:
            return False

        if 'postcards' not in self.session:
            self.session['postcards'] = {}

        self.session['postcards'][product_id_str] = {
            'id': str(postcard_id),  # ИСПРАВЛЕНО: приводим к строке
            'price': str(postcard_price),
            'title': postcard_title
        }
        self.save()
        # Обновляем локальную переменную
        self.postcards = self.session['postcards']
        return True

    def remove_postcard_from_product(self, product_id):
        """Удаляет открытку у товара"""
        product_id_str = str(product_id)
        if 'postcards' in self.session and product_id_str in self.session['postcards']:
            del self.session['postcards'][product_id_str]
            self.save()
            # Обновляем локальную переменную
            self.postcards = self.session.get('postcards', {})
            return True
        return False

    def get_postcard_total(self):
        """Возвращает общую стоимость всех открыток в корзине"""
        total = Decimal('0.00')
        for postcard_data in self.postcards.values():
            try:
                # ИСПРАВЛЕНО: Безопасное преобразование цены
                price_str = postcard_data.get('price', '0')
                # Убираем возможные символы валюты и пробелы
                price_str = price_str.replace('₽', '').replace('руб', '').replace(',', '.').strip()
                if price_str:
                    total += Decimal(price_str)
            except (ValueError, TypeError, AttributeError):
                continue
        return total

    # === МЕТОДЫ ДЛЯ ПРОМОКОДОВ ===

    @property
    def promo(self):
        """Возвращает объект промокода, если он есть"""
        if self.promo_id:
            try:
                return PromoCode.objects.get(id=self.promo_id)
            except PromoCode.DoesNotExist:
                return None
        return None

    def get_discount(self):
        """Считаем сумму скидки в рублях"""
        if self.promo:
            # (Процент / 100) * Общая сумма товаров (без учета открыток)
            return (Decimal(self.promo.discount) / Decimal(100)) * self.get_total_price()
        return Decimal(0)

    def get_total_price_after_discount(self):
        """Итоговая сумма к оплате (Товары - Скидка + Открытки)"""
        return self.get_total_price() - self.get_discount() + self.get_postcard_total()

    # ДОБАВЛЕНО: Метод для получения информации о товаре с открыткой
    def get_item_with_postcard(self, product_id):
        """Возвращает информацию о товаре с открыткой"""
        product_id_str = str(product_id)
        if product_id_str in self.cart:
            item = self.cart[product_id_str].copy()
            item['product_id'] = product_id
            item['postcard_info'] = self.postcards.get(product_id_str, {})
            item['postcard_text'] = self.postcard_texts.get(product_id_str, '')
            return item
        return None

    # ДОБАВЛЕНО: Метод для обновления текста открытки
    def update_postcard_text(self, product_id, text):
        """Обновляет текст открытки для товара"""
        product_id_str = str(product_id)
        if product_id_str in self.cart:
            if 'postcard_texts' not in self.session:
                self.session['postcard_texts'] = {}
            self.session['postcard_texts'][product_id_str] = text
            self.save()
            # Обновляем локальную переменную
            self.postcard_texts = self.session['postcard_texts']
            return True
        return False

    # ДОБАВЛЕНО: Метод для проверки, есть ли у товара открытка
    def has_postcard(self, product_id):
        """Проверяет, есть ли у товара открытка"""
        product_id_str = str(product_id)
        return product_id_str in self.postcards

    # ДОБАВЛЕНО: Метод для получения всех товаров с открытками
    def get_items_with_postcards(self):
        """Возвращает список товаров, у которых есть открытки"""
        items_with_postcards = []
        for item_id in self.cart.keys():
            if item_id in self.postcards:
                items_with_postcards.append(item_id)
        return items_with_postcards