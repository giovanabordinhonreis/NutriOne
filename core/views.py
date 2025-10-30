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
    context = {} 
    return render(request, 'core/dashboard_nutricionista.html', context)

# --- VIEWS DO CLIENTE ---
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
    proxima_consulta = Consulta.objects.filter( cliente=cliente, data_horario__gte=timezone.now(), status=Consulta.StatusChoices.CONFIRMADO ).order_by('data_horario').first()
    plano_atual = PlanoAlimentar.objects.filter( cliente=cliente ).order_by('-data_criacao').first()
    refeicoes_dict = {}
    if plano_atual:
        refeicoes = plano_atual.refeicoes.all()
        for refeicao in refeicoes:
            chave = refeicao.nome.lower().replace(" ", "_").replace("ç", "c").replace("ã", "a")
            refeicoes_dict[chave] = refeicao
    form_update = ClienteProfileUpdateForm(instance=cliente)
    context = { 'cliente': cliente, 'proxima_consulta': proxima_consulta, 'plano_atual': plano_atual, 'refeicoes': refeicoes_dict, 'form_update': form_update }
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
            form.save(); foto_url = cliente_profile.foto_perfil.url if cliente_profile.foto_perfil else None
            return JsonResponse({'success': True, 'foto_url': foto_url})
        else: return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    elif request.method == 'GET':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            data = { 'peso': cliente_profile.peso, 'altura': cliente_profile.altura, 'idade': cliente_profile.idade, 'objetivos': cliente_profile.objetivos, 'foto_url': cliente_profile.foto_perfil.url if cliente_profile.foto_perfil else None }
            return JsonResponse(data)
        else: return redirect('dashboard_cliente')
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def consultas_cliente(request):
    try:
        cliente = request.user.perfil_cliente
    except Cliente.DoesNotExist:
        return redirect('cadastro_cliente_perfil')
    now = timezone.now()
    consultas_futuras = Consulta.objects.filter( cliente=cliente, data_horario__gte=now ).order_by('data_horario')
    consultas_passadas = Consulta.objects.filter( cliente=cliente, data_horario__lt=now ).order_by('-data_horario')
    context = { 'consultas_futuras': consultas_futuras, 'consultas_passadas': consultas_passadas }
    return render(request, 'core/consultas_cliente.html', context)

@login_required
def encontrar_nutricionista(request):
    nutricionistas = Nutricionista.objects.filter(is_approved=True)
    especialidades = Especialidade.objects.all()
    especialidade_id = request.GET.get('especialidade')
    if especialidade_id:
        nutricionistas = nutricionistas.filter(especialidades__id=especialidade_id)
    context = { 'nutricionistas': nutricionistas, 'especialidades': especialidades, 'filtro_atual': int(especialidade_id) if especialidade_id else None }
    return render(request, 'core/encontrar_nutricionista.html', context)


# --- MUDANÇA NESSA VIEW ---
@login_required
def agendar_consulta(request, nutri_id):
    nutricionista = get_object_or_404(Nutricionista, id=nutri_id, is_approved=True)
    cliente = request.user.perfil_cliente

    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            try:
                consulta = form.save(commit=False)
                consulta.cliente = cliente
                consulta.nutricionista = nutricionista
                consulta.data_horario = form.cleaned_data['data_horario_selecionado']
                consulta.status = Consulta.StatusChoices.CONFIRMADO
                consulta.save() 
                return redirect('consultas_cliente')
            except IntegrityError:
                form.add_error(None, "Desculpe, este horário acabou de ser agendado. Por favor, escolha outro.")
    else: 
        form = ConsultaForm()

    context = {
        'nutricionista': nutricionista,
        'form': form,
        'today': timezone.now()  # <-- ADICIONA "HOJE" AO CONTEXTO
    }
    return render(request, 'core/agendar_consulta.html', context)
# --- FIM DA MUDANÇA ---


@login_required
def api_horarios_disponiveis(request):
    nutricionista_id = request.GET.get('nutri_id')
    data_selecionada_str = request.GET.get('data') 
    
    if not nutricionista_id or not data_selecionada_str:
        return JsonResponse({'error': 'Faltando parâmetros'}, status=400)

    try:
        nutri = Nutricionista.objects.get(id=nutricionista_id)
        data_selecionada = datetime.strptime(data_selecionada_str, '%Y-%m-%d').date()
        
        dia_semana_num = data_selecionada.weekday()
        dias_map = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        dia_semana_str = dias_map[dia_semana_num]

        horarios_dia = nutri.horarios_disponiveis.get(dia_semana_str)
        if not horarios_dia or not horarios_dia.get('inicio') or not horarios_dia.get('fim'):
            return JsonResponse({'horarios': []}) 

        inicio_str = horarios_dia['inicio']; fim_str = horarios_dia['fim']
        duracao = nutri.duracao_consulta
        hora_inicio = datetime.strptime(inicio_str, '%H:%M').time()
        hora_fim = datetime.strptime(fim_str, '%H:%M').time()

        consultas_marcadas = Consulta.objects.filter(
            nutricionista=nutri,
            data_horario__date=data_selecionada,
            status=Consulta.StatusChoices.CONFIRMADO
        ).values_list('data_horario', flat=True)
        
        horarios_ocupados = {consulta.time() for consulta in consultas_marcadas}

        horarios_disponiveis = []
        hora_atual = datetime.combine(data_selecionada, hora_inicio)
        hora_fim_dt = datetime.combine(data_selecionada, hora_fim)
        
        # Garante que só mostre horários no futuro (a partir de agora)
        agora = timezone.now()
        
        while hora_atual < hora_fim_dt:
            # Converte hora_atual para o timezone correto antes de comparar
            hora_atual_com_tz = timezone.make_aware(hora_atual, timezone.get_default_timezone())

            if hora_atual.time() not in horarios_ocupados and hora_atual_com_tz > agora:
                horarios_disponiveis.append({
                    'display': hora_atual.strftime('%H:%M'), 
                    'valor_iso': hora_atual.isoformat() 
                })
            hora_atual += timedelta(minutes=duracao)

        return JsonResponse({'horarios': horarios_disponiveis})

    except Nutricionista.DoesNotExist:
        return JsonResponse({'error': 'Nutricionista não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def planos_alimentares_cliente(request):
    return redirect('dashboard_cliente')