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
    path('nutricionista/perfil/', views.perfil_nutricionista_ajax, name='perfil_nutri_ajax'),
    path('nutricionista/meus-clientes/', views.clientes_nutricionista, name='clientes_nutri'),
    path('nutricionista/agenda/', views.agenda_nutricionista, name='agenda_nutri'),
    path('nutricionista/cliente/<int:cliente_id>/novo-plano/', views.criar_plano_alimentar, name='criar_plano'),
    path('consulta/cancelar/<int:consulta_id>/', views.cancelar_consulta_nutri, name='cancelar_consulta_nutri'),
    path('api/cliente-detalhes/<int:cliente_id>/', views.api_cliente_detalhes, name='api_cliente_detalhes'),
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('cliente/perfil/', views.perfil_cliente, name='perfil_cliente'),
    path('cliente/consultas/', views.consultas_cliente, name='consultas_cliente'),
    path('cliente/encontrar-nutri/', views.encontrar_nutricionista, name='encontrar_nutricionista'),
    path('cliente/agendar/<int:nutri_id>/', views.agendar_consulta, name='agendar_consulta'),
    path('cliente/api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
    path('cliente/planos/', views.planos_alimentares_cliente, name='planos_alimentares_cliente'),
    path('cliente/plano/nutricionista/<int:nutri_id>/', views.plano_por_nutricionista, name='plano_por_nutricionista'),
    path('cliente/consulta/<int:consulta_id>/cancelar/', views.cancelar_consulta, name='cancelar_consulta'),
]