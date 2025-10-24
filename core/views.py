from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse 
from django.views.decorators.http import require_POST 
from django.utils import timezone 

from .forms import (
    CustomAuthenticationForm, 
    CustomUserCreationForm, 
    NutricionistaProfileForm,
    ClienteProfileForm,
    ClienteProfileUpdateForm 
)
from .models import Nutricionista, Cliente, User, Consulta, PlanoAlimentar, Refeicao 


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
            else: return redirect('selecionar_conta')
    else: form = CustomAuthenticationForm()
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
    else: form = CustomUserCreationForm()
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
            cd = form.cleaned_data; horarios = {}
            dias = ['segunda','terca','quarta','quinta','sexta','sabado']
            for dia in dias:
                if cd[f'{dia}_ativo']:
                    horarios[dia] = { 'inicio': cd[f'{dia}_inicio'].strftime('%H:%M') if cd[f'{dia}_inicio'] else None, 'fim': cd[f'{dia}_fim'].strftime('%H:%M') if cd[f'{dia}_fim'] else None }
            nutri, created = Nutricionista.objects.update_or_create( usuario=request.user, defaults={ 'preco_consulta': cd['preco_consulta'], 'duracao_consulta': cd['duracao_consulta'], 'horarios_disponiveis': horarios })
            nutri.especialidades.set(cd['especialidades']); user = request.user
            user.user_type = User.UserType.NUTRICIONISTA; user.save()
            return redirect('dashboard_nutri')
    else: form = NutricionistaProfileForm()
    return render(request, 'core/cadastro_nutricionista.html', {'form': form})

@login_required
def dashboard_nutricionista(request):
    context = {} 
    return render(request, 'core/dashboard_nutricionista.html', context)


@login_required
def cadastro_cliente_perfil(request):
    if request.method == 'POST':
        form = ClienteProfileForm(request.POST) 
        if form.is_valid():
            cliente, created = Cliente.objects.update_or_create( usuario=request.user, defaults=form.cleaned_data )
            user = request.user; user.user_type = User.UserType.CLIENTE; user.save()
            return redirect('dashboard_cliente')
    else: form = ClienteProfileForm()
    return render(request, 'core/cadastro_cliente_perfil.html', {'form': form})

@login_required
def dashboard_cliente(request):
    try:
        cliente = request.user.perfil_cliente
    except Cliente.DoesNotExist:
        return redirect('cadastro_cliente_perfil')

    proxima_consulta = Consulta.objects.filter(
        cliente=cliente, 
        data_horario__gte=timezone.now(),
        status=Consulta.StatusChoices.CONFIRMADO
    ).order_by('data_horario').first()

    plano_atual = PlanoAlimentar.objects.filter(
        cliente=cliente
    ).order_by('-data_criacao').first()

    refeicoes_dict = {}
    if plano_atual:
        refeicoes = plano_atual.refeicoes.all()
        for refeicao in refeicoes:
            chave = refeicao.nome.lower().replace(" ", "_").replace("ç", "c").replace("ã", "a")
            refeicoes_dict[chave] = refeicao
    
    
    form_update = ClienteProfileUpdateForm(instance=cliente)

    context = {
        'cliente': cliente,
        'proxima_consulta': proxima_consulta, 
        'plano_atual': plano_atual,         
        'refeicoes': refeicoes_dict,        
        'form_update': form_update 
    }
    return render(request, 'core/dashboard_cliente.html', context)


@login_required
def perfil_cliente(request):

    try:
        cliente_profile = request.user.perfil_cliente
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Perfil não encontrado.'}, status=404)

    if request.method == 'POST':
        form = ClienteProfileUpdateForm(request.POST, request.FILES, instance=cliente_profile)
        if form.is_valid():
            form.save() 
            foto_url = cliente_profile.foto_perfil.url if cliente_profile.foto_perfil else None
            return JsonResponse({'success': True, 'foto_url': foto_url})
        else:
            # Retorna erros de validação
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
    elif request.method == 'GET':

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':

            data = {
                'peso': cliente_profile.peso,
                'altura': cliente_profile.altura,
                'idade': cliente_profile.idade,
                'objetivos': cliente_profile.objetivos, 
                'foto_url': cliente_profile.foto_perfil.url if cliente_profile.foto_perfil else None 
            }
            
            return JsonResponse(data)
        else:
            
            return redirect('dashboard_cliente')

    
    return JsonResponse({'error': 'Método não permitido'}, status=405)



@login_required
def consultas_cliente(request): return redirect('dashboard_cliente')
@login_required
def planos_alimentares_cliente(request): return redirect('dashboard_cliente')
@login_required
def encontrar_nutricionista(request): return redirect('dashboard_cliente')