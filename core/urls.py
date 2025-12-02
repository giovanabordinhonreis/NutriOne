from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_usuario, name='login'),  
    path('logout/', views.logout_usuario, name='logout'),
    path('cadastro/', views.cadastro_cliente, name='cadastro_cliente'),
    path('selecionar-conta/', views.selecionar_conta, name='selecionar_conta'),
    path('nutricionista/cadastro/', views.cadastro_nutricionista, name='cadastro_nutricionista'),
    path('nutricionista/dashboard/', views.dashboard_nutricionista_today, name='dashboard_nutri'),
    path('nutricionista/dashboard/<str:date_str>/', views.dashboard_nutricionista, name='dashboard_nutri_date'),
    path('nutricionista/perfil/', views.perfil_nutricionista, name='perfil_nutricionista'),
    path('cliente/meus-planos/', views.planos_alimentares_cliente, name='planos_alimentares_cliente'),
    path('nutricionista/meus-clientes/', views.meus_clientes, name='meus_clientes'),
    path('nutricionista/api/cliente/<int:cliente_id>/', views.api_cliente_detalhes, name='api_cliente_detalhes'),
    path('cliente/plano-nutri/<int:nutri_id>/', views.plano_por_nutricionista, name='plano_por_nutricionista'),
    path('nutricionista/cliente/<int:cliente_id>/plano/', views.criar_plano_alimentar, name='criar_plano_alimentar'),
    path('nutricionista/consulta/<int:consulta_id>/cancelar/', views.cancelar_consulta_nutri, name='cancelar_consulta_nutri'),
    path('cliente/cadastro-perfil/', views.cadastro_cliente_perfil, name='cadastro_cliente_perfil'),
    path('cliente/dashboard/', views.dashboard_cliente, name='dashboard_cliente'),
    path('cliente/perfil/', views.perfil_cliente, name='perfil_cliente'),
    path('cliente/consultas/', views.consultas_cliente, name='consultas_cliente'),
    path('cliente/encontrar-nutricionista/', views.encontrar_nutricionista, name='encontrar_nutricionista'),
    path('cliente/agendar/<int:nutri_id>/', views.agendar_consulta, name='agendar_consulta'),
    path('cliente/cancelar/<int:consulta_id>/', views.cancelar_consulta, name='cancelar_consulta'),
    path('api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
]