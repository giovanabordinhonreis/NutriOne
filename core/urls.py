from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_usuario, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
]