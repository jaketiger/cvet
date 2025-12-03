from django.urls import path
from . import views

app_name = 'promo'

urlpatterns = [
    path('apply/', views.apply_promo, name='apply'),
]