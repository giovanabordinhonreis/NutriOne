from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse 
from django.views.decorators.http import require_POST 
from django.utils import timezone 
from django.db.models import Q 
from django.db import IntegrityError, transaction
from datetime import datetime, time, timedelta 
import unicodedata

from .forms import (
    CustomAuthenticationForm, CustomUserCreationForm, NutricionistaProfileForm,
    ClienteProfileForm, ClienteProfileUpdateForm, ConsultaForm, NutricionistaProfileUpdateForm
)
from .models import (
    Nutricionista, Cliente, User, Consulta,
    PlanoAlimentar, Refeicao, Especialidade
)


def normalizar_nome_refeicao(nome):
    if not nome:
        return ""
    
    nfkd_form = unicodedata.normalize('NFKD', nome)
    nome_sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    return nome_sem_acentos.lower().replace(" ", "_").replace("-", "_")



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
            nutri.especialidades.set([cd['especialidades']]); user = request.user
            user.user_type = User.UserType.NUTRICIONISTA; user.save()
            nutri.is_approved = True
            nutri.save()
            return redirect('dashboard_nutri')
    else: form = NutricionistaProfileForm()
    return render(request, 'core/cadastro_nutricionista.html', {'form': form})

@login_required
def dashboard_nutricionista_today(request):
    today_str = timezone.now().strftime('%Y-%m-%d')
    return redirect('dashboard_nutri_date', date_str=today_str)

@login_required
def dashboard_nutricionista(request, date_str):
    try:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        today_str = timezone.now().strftime('%Y-%m-%d')
        return redirect('dashboard_nutri_date', date_str=today_str)

    today = timezone.now().date()
    previous_day = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
    next_day = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
    limit_date = today + timedelta(days=7)
    next_day_disabled = current_date >= limit_date

    try:
        nutri_profile = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return redirect('cadastro_nutricionista')

    appointments = Consulta.objects.filter(
        nutricionista=nutri_profile,
        data_horario__date=current_date
    ).order_by('data_horario')
    
    form_update_nutri = NutricionistaProfileUpdateForm(instance=nutri_profile)

    context = {
        'appointments': appointments,
        'current_date': current_date,
        'previous_day_url': previous_day,
        'next_day_url': next_day,
        'next_day_disabled': next_day_disabled,
        'is_today': current_date == today,
        'form_update_nutri': form_update_nutri
    }
    
    return render(request, 'core/dashboard_nutricionista.html', context)

@login_required
def perfil_nutricionista(request):
    try:
        nutri_profile = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return JsonResponse({'error': 'Perfil de nutricionista não encontrado.'}, status=404)

    if request.method == 'POST':
        form = NutricionistaProfileUpdateForm(request.POST, request.FILES, instance=nutri_profile)
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
            
            nutri_profile = form.save(commit=False)
            nutri_profile.horarios_disponiveis = horarios
            nutri_profile.save()
            
            nutri_profile.especialidades.set([cd['especialidades']])
            
            foto_url = nutri_profile.foto_perfil.url if nutri_profile.foto_perfil else None
            return JsonResponse({'success': True, 'foto_url': foto_url})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    elif request.method == 'GET':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            dados = {
                'preco_consulta': nutri_profile.preco_consulta,
                'duracao_consulta': nutri_profile.duracao_consulta,
                'especialidades': nutri_profile.especialidades.first().id if nutri_profile.especialidades.exists() else None,
                'horarios': nutri_profile.horarios_disponiveis or {},
                'foto_url': nutri_profile.foto_perfil.url if nutri_profile.foto_perfil else None
            }
            return JsonResponse(dados)
        else:
            return redirect('dashboard_nutri')
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def meus_clientes(request):
    try:
        nutri_profile = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return redirect('cadastro_nutricionista')

    client_ids = Consulta.objects.filter(nutricionista=nutri_profile).values_list('cliente', flat=True).distinct()
    clientes_list = Cliente.objects.filter(id__in=client_ids)

    search_query = request.GET.get('nome_cliente', '')
    if search_query:
        clientes_list = clientes_list.filter(
            Q(usuario__first_name__icontains=search_query) |
            Q(usuario__last_name__icontains=search_query)
        )

    context = {
        'clientes': clientes_list,
        'search_query': search_query,
    }
    return render(request, 'core/meus_clientes.html', context)


@login_required
def cadastro_cliente_perfil(request):
    if request.method == 'POST':
        form = ClienteProfileForm(request.POST, request.FILES)
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
            # --- MUDANÇA AQUI: Usa a nova função de normalização ---
            chave = normalizar_nome_refeicao(refeicao.nome)
            refeicoes_dict[chave] = refeicao
            # --- FIM DA MUDANÇA ---
            
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

@login_required
def agendar_consulta(request, nutri_id):
    nutricionista = get_object_or_404(Nutricionista, id=nutri_id, is_approved=True)
    try:
        cliente = request.user.perfil_cliente
    except Cliente.DoesNotExist:
        return redirect('cadastro_cliente_perfil')

    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            try:
                consulta = form.save(commit=False); consulta.cliente = cliente; consulta.nutricionista = nutricionista
                consulta.data_horario = form.cleaned_data['data_horario_selecionado']
                consulta.status = Consulta.StatusChoices.CONFIRMADO; consulta.save() 
                return redirect('consultas_cliente')
            except IntegrityError:
                form.add_error(None, "Desculpe, este horário acabou de ser agendado. Por favor, escolha outro.")
    else:
        form = ConsultaForm()

    context = {
        'nutricionista': nutricionista,
        'form': form,
        'today': timezone.now()
    }
    return render(request, 'core/agendar_consulta.html', context)

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
        
        agora = timezone.now()
        while hora_atual < hora_fim_dt:
            hora_atual_com_tz = timezone.make_aware(hora_atual, timezone.get_default_timezone())
            if hora_atual.time() not in horarios_ocupados and hora_atual_com_tz > agora:
                horarios_disponiveis.append({ 'display': hora_atual.strftime('%H:%M'), 'valor_iso': hora_atual.isoformat() })
            hora_atual += timedelta(minutes=duracao)
        return JsonResponse({'horarios': horarios_disponiveis})
    except Nutricionista.DoesNotExist:
        return JsonResponse({'error': 'Nutricionista não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def planos_alimentares_cliente(request):
    try:
        cliente = request.user.perfil_cliente
    except Cliente.DoesNotExist:
        return redirect('cadastro_cliente_perfil')

    plano_atual = PlanoAlimentar.objects.filter(
        cliente=cliente
    ).order_by('-data_criacao').first()
    
    refeicoes = []
    if plano_atual:
        refeicoes = plano_atual.refeicoes.all().order_by('id') 

    form_update = ClienteProfileUpdateForm(instance=cliente)

    context = {
        'plano_atual': plano_atual,
        'refeicoes': refeicoes, 
        'form_update': form_update,
    }
    
    return render(request, 'core/planos_alimentares_cliente.html', context)

@login_required
def api_cliente_detalhes(request, cliente_id):
    try:
        nutri_profile = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    cliente = get_object_or_404(Cliente, id=cliente_id, consulta__nutricionista=nutri_profile)

    consultas_futuras = Consulta.objects.filter(
        cliente=cliente,
        nutricionista=nutri_profile,
        data_horario__gte=timezone.now()
    ).order_by('data_horario')[:5]

    consultas_list = []
    for consulta in consultas_futuras:
        consultas_list.append({
            'data': consulta.data_horario.strftime('%d/%m/%Y'),
            'hora': consulta.data_horario.strftime('%H:%M'),
            'modalidade': consulta.get_modalidade_display(),
            'status': consulta.get_status_display()
        })

    dados = {
        'nome': cliente.usuario.get_full_name(),
        'foto_url': cliente.foto_perfil.url if cliente.foto_perfil else "{% static 'core/images/placeholder_cliente.png' %}",
        'peso': f"{cliente.peso} kg" if cliente.peso else "Não informado",
        'altura': f"{cliente.altura} m" if cliente.altura else "Não informado",
        'idade': f"{cliente.idade} anos" if cliente.idade else "Não informado",
        'objetivos': cliente.objetivos if cliente.objetivos else "Não informado",
        'consultas': consultas_list
    }
    
    return JsonResponse(dados)