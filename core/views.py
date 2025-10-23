from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from .forms import CustomAuthenticationForm, CustomUserCreationForm, NutricionistaProfileForm
from .models import Nutricionista

def login_usuario(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('selecionar_conta') 
    else:
        form = CustomAuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

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
            
            nutri_profile.especialidades.clear()
            nutri_profile.especialidades.add(cd['especialidades'])
            
            return redirect('dashboard_nutri')
    else:
        form = NutricionistaProfileForm()
        
    return render(request, 'core/cadastro_nutricionista.html', {'form': form})

@login_required
def dashboard_nutricionista(request):
    return render(request, 'core/dashboard_nutricionista.html')