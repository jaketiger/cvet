# promo/views.py

from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import PromoCode
from .forms import PromoApplyForm


@require_POST
def apply_promo(request):
    now = timezone.now()
    form = PromoApplyForm(request.POST)

    if form.is_valid():
        code = form.cleaned_data['code']
        try:
            # Ищем активный промокод, попадающий в диапазон дат
            promo = PromoCode.objects.get(
                code__iexact=code,  # iexact = регистр не важен (Code = code)
                valid_from__lte=now,
                valid_to__gte=now,
                active=True
            )
            # Сохраняем ID промокода в сессию пользователя
            request.session['promo_id'] = promo.id
            messages.success(request, f"Промокод {promo.code} применен! Скидка {promo.discount}%")
        except PromoCode.DoesNotExist:
            request.session['promo_id'] = None
            messages.error(request, "Промокод не найден, истек или неактивен.")

    return redirect('cart:cart_detail')