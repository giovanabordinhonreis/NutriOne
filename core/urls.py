from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_usuario, name='login'),
    path('cadastro/', views.cadastro_cliente, name='cadastro'),
    path('selecionar-conta/', views.selecionar_conta, name='selecionar_conta'),
    path('cadastro/nutricionista/', views.cadastro_nutricionista, name='cadastro_nutricionista'),
    path('dashboard/nutricionista/', views.dashboard_nutricionista, name='dashboard_nutri'),
    path('cadastro/cliente/', views.cadastro_cliente_etapa2, name='cadastro_cliente_etapa2'),
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
]