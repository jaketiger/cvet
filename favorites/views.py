# favorites/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from shop.models import Product
from .favorites import Favorites


def favorites_list(request):
    favorites = Favorites(request)
    return render(request, 'favorites/list.html', {'favorites': favorites})


def toggle_favorite(request):
    # Используем POST запрос через AJAX
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        favorites = Favorites(request)

        # Если товар уже есть - удаляем, если нет - добавляем
        if favorites.has_product(product_id):
            favorites.remove(product)
            added = False
        else:
            favorites.add(product)
            added = True

        return JsonResponse({
            'success': True,
            'added': added,
            'count': len(favorites)
        })
    return JsonResponse({'success': False})