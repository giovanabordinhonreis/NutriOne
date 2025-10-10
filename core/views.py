# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from .forms import CustomAuthenticationForm, ClienteCreationForm

def login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('selecionar_conta') 
    else:
        form = CustomAuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def dashboard(request):
    return render(request, 'core/dashboard.html')

def cadastro_cliente(request):
    if request.method == 'POST':
        form = ClienteCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('selecionar_conta') 
    else:
        form = ClienteCreationForm()
    return render(request, 'core/cadastro.html', {'form': form})

@login_required 
def selecionar_conta(request):
    return render(request, 'core/selecionar_conta.html')