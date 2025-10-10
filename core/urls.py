# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('cadastro/', views.cadastro_cliente, name='cadastro'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('selecionar-conta/', views.selecionar_conta, name='selecionar_conta'),
]