# shop/views.py

from django.shortcuts import render, get_object_or_404
from .models import Category, Product, SiteSettings # <-- Добавлен импорт SiteSettings
from django.contrib.auth.decorators import login_required
from cart.forms import CartAddProductForm

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request,
                  'shop/product_list.html',
                  {'category': category,
                   'categories': categories,
                   'products': products})


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    return render(request,
                  'shop/product_detail.html',
                  {'product': product,
                   'cart_product_form': cart_product_form})


@login_required
def cabinet(request):
    orders = request.user.orders.all().order_by('-created')
    return render(request, 'shop/cabinet.html', {'orders': orders})


# --- НОВАЯ VIEW ДЛЯ СТРАНИЦЫ КОНТАКТОВ ---
def contact_page(request):
    # .get_solo() - это специальный метод django-solo для получения единственного объекта настроек
    site_settings = SiteSettings.get_solo()
    return render(request, 'shop/contacts.html', {'settings': site_settings})