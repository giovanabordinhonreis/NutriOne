from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('cadastro/', views.cadastro_cliente, name='cadastro'),
    path('dashboard/', views.dashboard, name='dashboard'),
]