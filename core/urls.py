from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('cadastro/nutricionista/', views.cadastro_nutricionista, name='cadastro_nutricionista'),
    path('cadastro/cliente/', views.cadastro_cliente_perfil, name='cadastro_cliente_perfil'),
    path('cadastro/', views.cadastro_cliente, name='cadastro'),
    path('selecionar-conta/', views.selecionar_conta, name='selecionar_conta'),
    path('dashboard/nutricionista/', views.dashboard_nutricionista_today, name='dashboard_nutri'),
    path('dashboard/nutricionista/<str:date_str>/', views.dashboard_nutricionista, name='dashboard_nutri_date'),
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('cliente/perfil/', views.perfil_cliente, name='perfil_cliente'),
    path('cliente/consultas/', views.consultas_cliente, name='consultas_cliente'),
    path('cliente/encontrar-nutri/', views.encontrar_nutricionista, name='encontrar_nutricionista'),
    path('cliente/agendar/<int:nutri_id>/', views.agendar_consulta, name='agendar_consulta'),
    path('cliente/api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
    path('cliente/planos/', views.planos_alimentares_cliente, name='planos_alimentares_cliente'),
    path('nutricionista/perfil/', views.perfil_nutricionista, name='perfil_nutricionista'),
    path('nutricionista/meus-clientes/', views.meus_clientes, name='meus_clientes'),
    # path('consulta/cancelar/<int:consulta_id>/', views.cancelar_consulta_nutri, name='cancelar_consulta_nutri'),
    path('api/cliente-detalhes/<int:cliente_id>/', views.api_cliente_detalhes, name='api_cliente_detalhes'),
]