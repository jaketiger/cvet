# users/views.py
from django.shortcuts import render, redirect
from .forms import RegistrationForm


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # <-- Теперь вся магия происходит внутри метода save() формы
            # Можно добавить сообщение "Вы успешно зарегистрировались!"
            return redirect('login')  # Перенаправляем на страницу входа
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})