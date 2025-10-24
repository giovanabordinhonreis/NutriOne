from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout 
from django.contrib.auth.decorators import login_required
from .forms import (
    CustomAuthenticationForm, 
    CustomUserCreationForm, 
    NutricionistaProfileForm,
    ClienteProfileForm
)
from .models import Nutricionista, Cliente, User

def login_usuario(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            if user.user_type == User.UserType.NUTRICIONISTA and hasattr(user, 'perfil_nutricionista'):
                return redirect('dashboard_nutri')
            elif user.user_type == User.UserType.CLIENTE and hasattr(user, 'perfil_cliente'):
                return redirect('dashboard_cliente')
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

@login_required
def cadastro_nutricionista(request):
    if request.method == 'POST':
        form = NutricionistaProfileForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            
            horarios = {}
            dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado']
            for dia in dias_semana:
                if cd[f'{dia}_ativo']:
                    horarios[dia] = {
                        'inicio': cd[f'{dia}_inicio'].strftime('%H:%M') if cd[f'{dia}_inicio'] else None,
                        'fim': cd[f'{dia}_fim'].strftime('%H:%M') if cd[f'{dia}_fim'] else None,
                    }
            
            nutri_profile, created = Nutricionista.objects.update_or_create(
                usuario=request.user,
                defaults={
                    'preco_consulta': cd['preco_consulta'],
                    'duracao_consulta': cd['duracao_consulta'],
                    'horarios_disponiveis': horarios
                }
            )
            
            nutri_profile.especialidades.set(cd['especialidades'])
            
            user = request.user
            user.user_type = User.UserType.NUTRICIONISTA
            user.save()

            return redirect('dashboard_nutri')
    else:
        form = NutricionistaProfileForm()
        
    return render(request, 'core/cadastro_nutricionista.html', {'form': form})

@login_required
def dashboard_nutricionista(request):
    return render(request, 'core/dashboard_nutricionista.html')

@login_required
def cadastro_cliente_perfil(request):
    if request.method == 'POST':
        form = ClienteProfileForm(request.POST)
        if form.is_valid():
            cliente_profile, created = Cliente.objects.update_or_create(
                usuario=request.user,
                defaults=form.cleaned_data
            )
            
            user = request.user
            user.user_type = User.UserType.CLIENTE
            user.save()
            
            return redirect('dashboard_cliente')
    else:
        form = ClienteProfileForm()
        
    return render(request, 'core/cadastro_cliente_perfil.html', {'form': form})

@login_required
def dashboard_cliente(request):
    try:
        cliente = request.user.perfil_cliente
    except Cliente.DoesNotExist:
        return redirect('cadastro_cliente_perfil')

    proxima_consulta = {
        'nutricionista': 'Ana Martins',
        'data_horario': 'Amanhã, 03 de Outubro de 2025 - 10:00',
        'modalidade': 'Online'
    }
    evolucao = {
        'peso_atual': '72.5',
        'imc': '22.5'
    }
    plano_hoje = {
        'cafe': {'nome': 'Café da Manhã', 'descricao': 'Aveia com frutas', 'calorias': 320},
        'almoco': {'nome': 'Almoço', 'descricao': 'Frango grelhado com arroz', 'calorias': 450},
        'lanche': {'nome': 'Lanche da Tarde', 'descricao': 'Iogurte com granola', 'calorias': 180},
        'jantar': {'nome': 'Jantar', 'descricao': 'Salmão com legumes', 'calorias': 380},
        'total_calorias': 1330,
        'meta_calorias': 1500,
    }
    
    progresso_percentual = 0
    if plano_hoje['meta_calorias'] > 0:
        progresso_percentual = (plano_hoje['total_calorias'] / plano_hoje['meta_calorias']) * 100

    context = {
        'cliente': cliente,
        'proxima_consulta': proxima_consulta,
        'evolucao': evolucao,
        'plano_hoje': plano_hoje,
        'progresso_percentual': progresso_percentual
    }
    return render(request, 'core/dashboard_cliente.html', context)

@login_required
def consultas_cliente(request):
    return redirect('dashboard_cliente')

@login_required
def planos_alimentares_cliente(request):
    return redirect('dashboard_cliente')

@login_required
def encontrar_nutricionista(request):
    return redirect('dashboard_cliente')

@login_required
def perfil_cliente(request):
    return redirect('dashboard_cliente')