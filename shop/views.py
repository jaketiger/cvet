# shop/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, Http404

# Импорты для поиска (PostgreSQL)
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, SearchHeadline

# Импорты моделей
from .models import Category, Product, SiteSettings, FooterPage, Banner, Benefit
from orders.models import Order

# Импорты форм
from cart.forms import CartAddProductForm
from users.forms import UserEditForm, ProfileEditForm

# Для асинхронных задач
from django_q.tasks import async_task


def search_results(request):
    """
    Поиск товаров с использованием полнотекстового поиска PostgreSQL.
    Ищет по названию, описанию и составу.
    """
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()

    if query:
        # Настройка векторов поиска
        search_vector = SearchVector('name', 'description', 'composition', config='russian')
        search_query = SearchQuery(query, config='russian')

        products = (
            Product.objects.annotate(
                rank=SearchRank(search_vector, search_query),
                highlighted_name=SearchHeadline(
                    'name',
                    search_query,
                    start_sel='<mark>',
                    stop_sel='</mark>',
                    config='russian'
                ),
                highlighted_description=SearchHeadline(
                    'description',
                    search_query,
                    start_sel='<mark>',
                    stop_sel='</mark>',
                    config='russian'
                ),
            )
            .filter(available=True)
            .filter(rank__gte=0.05)
            .order_by('-rank')
        )

    return render(request, 'shop/search_results.html', {'query': query, 'products': products})


def home_page(request):
    """
    Главная страница: баннеры и избранные товары.
    """
    featured_products = Product.objects.filter(is_featured=True, available=True)[:8]
    banners = Banner.objects.filter(is_active=True).order_by('order')

    return render(request, 'shop/home.html', {
        'featured_products': featured_products,
        'banners': banners,
    })


def product_list_all(request):
    """
    Каталог: Все товары.
    """
    products = Product.objects.filter(available=True)
    return render(request, 'shop/product_list.html', {'current_category': None, 'products': products})


def product_list_by_category(request, category_slug):
    """
    Каталог: Товары конкретной категории.
    """
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(available=True, category__slug=category_slug)
    return render(request, 'shop/product_list.html', {'current_category': category, 'products': products})


def product_detail(request, id, slug):
    """
    Карточка товара.
    """
    product = get_object_or_404(Product, id=id, slug=slug, available=True)

    # Загружаем активные преимущества (иконки) для отображения
    benefits = Benefit.objects.filter(is_active=True).order_by('order')

    # Форма добавления в корзину
    cart_product_form = CartAddProductForm()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'cart_product_form': cart_product_form,
        'benefits': benefits
    })


@login_required
def cabinet(request):
    """
    Личный кабинет пользователя: список заказов.
    """
    orders = request.user.orders.all().order_by('-created')
    return render(request, 'shop/cabinet.html', {'orders': orders})


@login_required
def profile_edit(request):
    """
    Редактирование профиля пользователя (Имя, Телефон, Адрес).
    """
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

    return render(request, 'shop/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


# === УМНЫЙ КОНТРОЛЛЕР СТРАНИЦ ФУТЕРА ===

def contact_page(request):
    """
    Редирект на единый обработчик страниц.
    """
    return redirect('shop:footer_page_detail', slug='contacts')


def footer_page_detail(request, slug):
    """
    Универсальное отображение страниц из футера.
    Работает как маршрутизатор: выбирает шаблон в зависимости от slug.
    """
    # Ищем страницу в базе
    page = FooterPage.objects.filter(slug=slug).first()
    site_settings = SiteSettings.get_solo()

    # Определяем заголовок
    custom_title = ""
    if page and page.page_title:
        custom_title = page.page_title
    elif page:
        custom_title = page.title
    else:
        # Дефолтные заголовки, если страницы нет в базе
        if slug == 'contacts':
            custom_title = site_settings.contacts_page_title or "Контакты"
        elif slug == 'about':
            custom_title = "О нас"
        elif slug == 'payment':
            custom_title = "Оплата и доставка"
        elif slug == 'terms':
            custom_title = "Договор оферты"

    # Если страницы нет и это не системный slug - 404
    if not page and slug not in ['contacts', 'about', 'payment', 'terms']:
        raise Http404("Страница не найдена")

    context = {
        'page': page,
        'custom_title': custom_title,
        'site_settings': site_settings
    }

    # Маршрутизация
    if slug == 'contacts':
        return render(request, 'shop/contacts.html', context)

    elif slug == 'about':
        return render(request, 'shop/about.html', context)

    elif slug == 'payment':
        return render(request, 'shop/payment.html', context)

    elif slug == 'terms':
        return render(request, 'shop/terms.html', context)

    # Обычная текстовая страница
    return render(request, 'shop/footer_page_detail.html', context)


@login_required
def order_detail(request, order_id):
    """
    Детальный просмотр заказа в личном кабинете.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})


@login_required
@require_POST
def cancel_order(request, order_id):
    """
    Отмена заказа пользователем.
    Возвращает товары на склад и отправляет уведомление админу.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.can_be_cancelled:
        # Возвращаем товары на склад
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()

        order.status = 'cancelled'
        order.save()

        # Отправка письма админу асинхронно
        base_url = f"{request.scheme}://{request.get_host()}"
        async_task('orders.utils.send_cancellation_email_task', order_id=order.id, base_url=base_url)

        messages.success(request, f'Заказ #{order.id} успешно отменен.')
    else:
        messages.error(request, 'Этот заказ уже нельзя отменить (он уже отправлен или доставлен).')

    return redirect('shop:order_detail', order_id=order.id)


@staff_member_required
def get_product_price(request):
    """
    API для получения цены товара (используется в админке или JS).
    """
    product_id = request.GET.get('product_id')
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            return JsonResponse({'price': str(product.price)})
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
    return JsonResponse({'error': 'No product_id provided'}, status=400)