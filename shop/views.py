# shop/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Category, Product, SiteSettings, FooterPage
from django.contrib.auth.decorators import login_required
from cart.forms import CartAddProductForm
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from users.forms import UserEditForm, ProfileEditForm
from django.contrib import messages
from orders.models import Order
from cart.cart import Cart
from django_q.tasks import async_task
from django.db.models import Func

# --- ИМПОРТЫ ДЛЯ ПОИСКА ---
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank,  SearchHeadline




def search_results(request):
    """
    Представление для полнотекстового поиска товаров.
    """
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()

    if query:
        search_vector = SearchVector('name', 'description', config='russian')
        # search_vector = SearchVector('name', config='russian') + SearchVector('description', config='russian')

        search_query = SearchQuery(query, config='russian')

        products = (
            Product.objects.annotate(
                rank=SearchRank(search_vector, search_query),
                highlighted_name=SearchHeadline('name', search_query, start_sel='<mark>', stop_sel='</mark>', config='russian'),
                highlighted_description=SearchHeadline('description', search_query, start_sel='<mark>', stop_sel='</mark>', config='russian'),
            )
            .filter(available=True)
            .filter(rank__gte=0.05)  # отсекаем нерелевантные результаты
            .order_by('-rank')
        )

    cart_product_form = CartAddProductForm()

    return render(request, 'shop/search_results.html', {
        'query': query,
        'products': products,
        # 'cart_product_form': cart_product_form,

    })


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


def product_list_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
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


@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль был успешно обновлен!')
            return redirect('shop:cabinet')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(request, 'shop/profile_edit.html', {'user_form': user_form, 'profile_form': profile_form})


def contact_page(request):
    site_settings = SiteSettings.get_solo()
    return render(request, 'shop/contacts.html', {'settings': site_settings})


def footer_page_detail(request, slug):
    page = get_object_or_404(FooterPage, slug=slug)
    return render(request, 'shop/footer_page_detail.html', {'page': page})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})


@login_required
@require_POST
def cancel_order(request, order_id):
    cart = Cart(request)
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.can_be_cancelled:
        for item in order.items.all():
            product = item.product
            if product:
                cart.add(product=product, quantity=item.quantity, update_quantity=True)
        order.status = 'cancelled'
        order.save()
        base_url = f"{request.scheme}://{request.get_host()}"
        async_task(
            'orders.utils.send_cancellation_email_task',
            order_id=order.id,
            base_url=base_url
        )
        messages.success(request,
                         f'Заказ #{order.id} был отменен. Товары возвращены в вашу корзину для редактирования.')
    else:
        messages.error(request, f'Этот заказ уже нельзя отменить.')
    return redirect('shop:cabinet')


@staff_member_required
def get_product_price(request):
    product_id = request.GET.get('product_id')
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            return JsonResponse({'price': str(product.price)})
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
    return JsonResponse({'error': 'No product_id provided'}, status=400)