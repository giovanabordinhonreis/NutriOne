from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse 
from django.views.decorators.http import require_POST 
from django.utils import timezone 
from django.db.models import Q 
from django.db import IntegrityError 
from datetime import datetime, time, timedelta 

from .forms import (
    CustomAuthenticationForm, CustomUserCreationForm, NutricionistaProfileForm,
    ClienteProfileForm, ClienteProfileUpdateForm, ConsultaForm 
)
from .models import (
    Nutricionista, Cliente, User, Consulta, 
    PlanoAlimentar, Refeicao, Especialidade
)

# --- VIEWS DE AUTENTICAÇÃO E CADASTRO (sem alterações) ---
def login_usuario(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            redirect_url = _redirecionar_usuario_completo(user)
            if redirect_url:
                return redirect(redirect_url) 
            else:
                return redirect('selecionar_conta')
            
    else:
        form = CustomAuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def logout_usuario(request):
    logout(request)
    return redirect('login')

def cadastro_cliente(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('selecionar_conta')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/cadastro.html', {'form': form})

@login_required 
def selecionar_conta(request):
    user = request.user
    if user.user_type == User.UserType.NUTRICIONISTA and hasattr(user, 'perfil_nutricionista'):
        return redirect('dashboard_nutri')
    elif user.user_type == User.UserType.CLIENTE and hasattr(user, 'perfil_cliente'):
        return redirect('dashboard_cliente')
    return render(request, 'core/selecionar_conta.html')

# --- VIEWS DO NUTRICIONISTA (sem alterações) ---
@login_required
def cadastro_nutricionista(request):
    if request.method == 'POST':
        form = NutricionistaProfileForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data; horarios = {}
            dias = ['segunda','terca','quarta','quinta','sexta','sabado']
            for dia in dias:
                if cd[f'{dia}_ativo']:
                    horarios[dia] = { 'inicio': cd[f'{dia}_inicio'].strftime('%H:%M') if cd[f'{dia}_inicio'] else None, 'fim': cd[f'{dia}_fim'].strftime('%H:%M') if cd[f'{dia}_fim'] else None }
            nutri, created = Nutricionista.objects.update_or_create( usuario=request.user, defaults={ 'preco_consulta': cd['preco_consulta'], 'duracao_consulta': cd['duracao_consulta'], 'horarios_disponiveis': horarios })
            nutri.especialidades.set(cd['especialidades']); user = request.user
            user.user_type = User.UserType.NUTRICIONISTA; user.save()
            nutri.is_approved = False 
            nutri.save()
            return redirect('dashboard_nutri')
    else: form = NutricionistaProfileForm()
    return render(request, 'core/cadastro_nutricionista.html', {'form': form})

@login_required
def dashboard_nutricionista(request):
    today = datetime.today().date()
    date_str = request.GET.get('date')

    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = today
    else:
        current_date = today

    min_date = today - timedelta(days=7)
    max_date = today + timedelta(days=7)

    if current_date < min_date:
        current_date = min_date
    elif current_date > max_date:
        current_date = max_date

    prev_date = max(current_date - timedelta(days=1), min_date)
    next_date = min(current_date + timedelta(days=1), max_date)

    appointments = [] 

    context = {
        'current_date': current_date,
        'prev_date': prev_date.strftime('%Y-%m-%d'),
        'next_date': next_date.strftime('%Y-%m-%d'),
        'appointments': appointments,
        'min_date': min_date.strftime('%Y-%m-%d'),
        'max_date': max_date.strftime('%Y-%m-%d'),
    }

    return render(request, 'core/dashboard_nutricionista.html', context)
@login_required
def cadastro_cliente_etapa2(request):
    if request.method == 'POST':
        form = ClienteProfileForm(request.POST)
        if form.is_valid():
            profile, created = Cliente.objects.update_or_create(
                usuario=request.user,
                defaults=form.cleaned_data
            )
            return redirect('dashboard_cliente')
    else:
        form = ClienteProfileForm()
    
    return render(request, 'core/cadastro_cliente_etapa2.html', {'form': form})

@login_required
def dashboard_cliente(request):
    return render(request, 'core/dashboard_cliente.html')
def _redirecionar_usuario_completo(user):
    if hasattr(user, 'perfil_nutricionista'):
        return 'dashboard_nutri'
    if hasattr(user, 'perfil_cliente'):
        return 'dashboard_cliente'
    return None