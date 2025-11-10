# shop/views.py

from django.shortcuts import render, get_object_or_404
from .models import Category, Product, SiteSettings
from django.contrib.auth.decorators import login_required
from cart.forms import CartAddProductForm

def home_page(request):
    site_settings = SiteSettings.get_solo()
    featured_products = Product.objects.filter(is_featured=True, available=True)[:8]
    return render(request, 'shop/home.html', {
        'settings': site_settings,
        'featured_products': featured_products,
    })

def product_list_all(request):
    products = Product.objects.filter(available=True)
    return render(request, 'shop/product_list.html', {
        'current_category': None,
        'products': products
    })

# --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
def product_list_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    # Используем '__slug' для фильтрации по slug'у связанной категории
    products = Product.objects.filter(available=True, category__slug=category_slug)
    return render(request, 'shop/product_list.html', {
        'current_category': category,
        'products': products
    })

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

def contact_page(request):
    site_settings = SiteSettings.get_solo()
    return render(request, 'shop/contacts.html', {'settings': site_settings})

# --- НОВЫЕ VIEWS ДЛЯ СТАТИЧЕСКИХ СТРАНИЦ ---
def about_page(request):
    site_settings = SiteSettings.get_solo()
    return render(request, 'shop/about.html', {'settings': site_settings})

def payment_page(request):
    site_settings = SiteSettings.get_solo()
    return render(request, 'shop/payment.html', {'settings': site_settings})

def terms_page(request):
    site_settings = SiteSettings.get_solo()
    return render(request, 'shop/terms.html', {'settings': site_settings})