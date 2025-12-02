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
    ClienteProfileForm, ClienteProfileUpdateForm, ConsultaForm,
    NutricionistaProfileUpdateForm, PlanoAlimentarForm, RefeicaoForm
)
from .models import (
    Nutricionista, Cliente, User, Consulta, 
    PlanoAlimentar, Refeicao, Especialidade
)
from django.forms import inlineformset_factory 


def normalizar_nome_refeicao(nome):
    if not nome: return ""
    nfkd_form = unicodedata.normalize('NFKD', nome)
    nome_sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return nome_sem_acentos.lower().replace(" ", "_").replace("-", "_")


def atualizar_status_automatico(nutricionista):
    """
    Verifica todas as consultas desse nutricionista.
    Se a data/hora já passou e ainda está 'CONFIRMADO', muda para 'CONCLUIDO'.
    """
    agora = timezone.now()
    consultas_vencidas = Consulta.objects.filter(
        nutricionista=nutricionista,
        data_horario__lt=agora,
        status=Consulta.StatusChoices.CONFIRMADO
    )
    if consultas_vencidas.exists():
        consultas_vencidas.update(status=Consulta.StatusChoices.CONCLUIDO)


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
        form = NutricionistaProfileForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            horarios = {}
            dias = ['segunda','terca','quarta','quinta','sexta','sabado']
            for dia in dias:
                if cd.get(f'{dia}_ativo'):
                    horarios[dia] = { 'inicio': cd[f'{dia}_inicio'].strftime('%H:%M') if cd.get(f'{dia}_inicio') else None, 'fim': cd[f'{dia}_fim'].strftime('%H:%M') if cd.get(f'{dia}_fim') else None }
            
            nutri, created = Nutricionista.objects.update_or_create(
                usuario=request.user, 
                defaults={ 
                    'preco_consulta': cd['preco_consulta'], 
                    'duracao_consulta': cd['duracao_consulta'], 
                    'horarios_disponiveis': horarios,
                    'foto_perfil': cd.get('foto_perfil')
                }
            )
            nutri.especialidades.set(cd['especialidades'])
            
            user = request.user
            user.user_type = User.UserType.NUTRICIONISTA
            user.save()
            nutri.is_approved = False 
            nutri.save()
            return redirect('dashboard_nutri')
    else: form = NutricionistaProfileForm()
    return render(request, 'core/cadastro_nutricionista.html', {'form': form})

@login_required
def dashboard_nutricionista_today(request):
    today_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d')
    return redirect('dashboard_nutri_date', date_str=today_str)

@login_required
def dashboard_nutricionista(request, date_str):
    try:
        nutri_profile = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return redirect('cadastro_nutricionista')

    atualizar_status_automatico(nutri_profile)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localtime(timezone.now()).date()
        return redirect('dashboard_nutri_date', date_str=selected_date.strftime('%Y-%m-%d'))

    today = timezone.localtime(timezone.now()).date()

    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    prev_week_url = (start_of_week - timedelta(days=7)).strftime('%Y-%m-%d')
    next_week_url = (start_of_week + timedelta(days=7)).strftime('%Y-%m-%d')

    consultas_semana = Consulta.objects.filter(
        nutricionista=nutri_profile,
        data_horario__date__range=[start_of_week, end_of_week]
    )

    agenda_semanal = []
    for i in range(7):
        dia_iteracao = start_of_week + timedelta(days=i)
        
        tem_consultas = consultas_semana.filter(data_horario__date=dia_iteracao).exists()
        
        agenda_semanal.append({
            'data': dia_iteracao,
            'dia_numero': dia_iteracao.day,
            'is_selected': dia_iteracao == selected_date,
            'is_today': dia_iteracao == today,           
            'tem_consultas': tem_consultas,               
            'url': dia_iteracao.strftime('%Y-%m-%d')      
        })

    appointments = Consulta.objects.filter(
        nutricionista=nutri_profile,
        data_horario__date=selected_date 
    ).order_by('data_horario')

    form_update_nutri = NutricionistaProfileUpdateForm(instance=nutri_profile)

    context = {
        'agenda_semanal': agenda_semanal,
        'appointments': appointments,
        'selected_date': selected_date,
        'today': today,
        'prev_week_url': prev_week_url,
        'next_week_url': next_week_url,
        'form_update_nutri': form_update_nutri,
        'is_today_view': selected_date == today
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
            perfil_salvo = form.save(commit=False)
            
            horarios = {}
            dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado']
            for dia in dias_semana:
                if cd.get(f'{dia}_ativo'):
                    horarios[dia] = { 
                        'inicio': cd[f'{dia}_inicio'].strftime('%H:%M') if cd.get(f'{dia}_inicio') else None, 
                        'fim': cd[f'{dia}_fim'].strftime('%H:%M') if cd.get(f'{dia}_fim') else None, 
                    }
            perfil_salvo.horarios_disponiveis = horarios
            perfil_salvo.save()
            
            if 'especialidades' in cd:
                nutri_profile.especialidades.set(cd['especialidades'])
            
            foto_url = perfil_salvo.foto_perfil.url if perfil_salvo.foto_perfil else None
            return JsonResponse({'success': True, 'foto_url': foto_url})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        todas_especialidades = list(Especialidade.objects.values('id', 'nome'))
        minhas_especialidades = list(nutri_profile.especialidades.values_list('id', flat=True))

        data = {
            'preco_consulta': nutri_profile.preco_consulta,
            'duracao_consulta': nutri_profile.duracao_consulta,
            'horarios': nutri_profile.horarios_disponiveis or {},
            'foto_url': nutri_profile.foto_perfil.url if nutri_profile.foto_perfil else None,
            'todas_especialidades': todas_especialidades,
            'minhas_especialidades': minhas_especialidades
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def agenda_nutricionista(request):
    try: nutri = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist: return redirect('cadastro_nutricionista')
    now = timezone.now()
    consultas_futuras = Consulta.objects.filter( nutricionista=nutri, data_horario__gte=now, status=Consulta.StatusChoices.CONFIRMADO ).order_by('data_horario')
    consultas_passadas = Consulta.objects.filter( nutricionista=nutri, data_horario__lt=now ).order_by('-data_horario')
    form_update = NutricionistaProfileUpdateForm(instance=nutri)
    context = { 'consultas_futuras': consultas_futuras, 'consultas_passadas': consultas_passadas, 'form_update': form_update }
    return render(request, 'core/agenda_nutricionista.html', context)

@login_required
def clientes_nutricionista(request):
    try: nutri = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist: return redirect('cadastro_nutricionista')
    cliente_ids = Consulta.objects.filter( nutricionista=nutri ).values_list('cliente__id', flat=True).distinct()
    meus_clientes = Cliente.objects.filter(id__in=cliente_ids)
    form_update = NutricionistaProfileUpdateForm(instance=nutri)
    context = { 'meus_clientes': meus_clientes, 'form_update': form_update }
    return render(request, 'core/clientes_nutricionista.html', context)

@login_required
def meus_clientes(request):
    try:
        nutri_profile = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return redirect('cadastro_nutricionista')

    atualizar_status_automatico(nutri_profile)

    client_ids = Consulta.objects.filter(nutricionista=nutri_profile).values_list('cliente', flat=True).distinct()
    clientes_list = Cliente.objects.filter(id__in=client_ids)

    for cliente in clientes_list:
        cliente.tem_plano = PlanoAlimentar.objects.filter(cliente=cliente, nutricionista=nutri_profile).exists()

    search_query = request.GET.get('nome_cliente', '')
    if search_query:
        clientes_list = clientes_list.filter(
            Q(usuario__first_name__icontains=search_query) |
            Q(usuario__last_name__icontains=search_query)
        )
    
    form_update_nutri = NutricionistaProfileUpdateForm(instance=nutri_profile)

    context = { 
        'clientes': clientes_list, 
        'search_query': search_query,
        'form_update_nutri': form_update_nutri 
    }
    return render(request, 'core/meus_clientes.html', context)

@login_required
def api_cliente_detalhes(request, cliente_id):
    try:
        nutri_profile = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    atualizar_status_automatico(nutri_profile)

    todas_consultas = Consulta.objects.filter(
        cliente=cliente,
        nutricionista=nutri_profile
    ).order_by('-data_horario')

    consultas_list = []
    for consulta in todas_consultas:
        consultas_list.append({
            'data': consulta.data_horario.strftime('%d/%m/%Y'),
            'hora': consulta.data_horario.strftime('%H:%M'),
            'modalidade': consulta.get_modalidade_display(),
            'status': consulta.get_status_display()
        })

    dados = {
        'nome': cliente.usuario.get_full_name(),
        'foto_url': cliente.foto_perfil.url if cliente.foto_perfil else "/static/core/images/placeholder_cliente.png",
        'peso': f"{cliente.peso} kg" if cliente.peso else "Não informado",
        'altura': f"{cliente.altura} m" if cliente.altura else "Não informado",
        'idade': f"{cliente.idade} anos" if cliente.idade else "Não informado",
        'objetivos': cliente.objetivos if cliente.objetivos else "Não informado",
        'consultas': consultas_list
    }
    return JsonResponse(dados)

@login_required
@require_POST
def cancelar_consulta_nutri(request, consulta_id):
    try:
        nutri_profile = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return redirect('login')

    consulta = get_object_or_404(Consulta, id=consulta_id, nutricionista=nutri_profile)
    consulta.status = Consulta.StatusChoices.CANCELADO
    consulta.save()
    
    data_str = consulta.data_horario.strftime('%Y-%m-%d')
    return redirect('dashboard_nutri_date', date_str=data_str)

@login_required
@transaction.atomic
def criar_plano_alimentar(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    nutricionista = request.user.perfil_nutricionista
    
    plano_existente = PlanoAlimentar.objects.filter(cliente=cliente, nutricionista=nutricionista).first()

    extra_forms = 4 if plano_existente is None else 0

    RefeicaoFormSet = inlineformset_factory(
        PlanoAlimentar, 
        Refeicao, 
        form=RefeicaoForm, 
        extra=extra_forms, 
        can_delete=True
    )

    if request.method == 'POST':
        form_plano = PlanoAlimentarForm(request.POST, instance=plano_existente)
        formset_refeicoes = RefeicaoFormSet(request.POST, instance=plano_existente)

        if form_plano.is_valid() and formset_refeicoes.is_valid():
            plano = form_plano.save(commit=False)
            plano.cliente = cliente
            plano.nutricionista = nutricionista
            plano.save()
            
            formset_refeicoes.instance = plano
            formset_refeicoes.save()
            
            plano.refeicoes.filter(nome__exact='').delete()
            
            return redirect('meus_clientes')
    else:
        form_plano = PlanoAlimentarForm(instance=plano_existente)
        formset_refeicoes = RefeicaoFormSet(instance=plano_existente)

    context = {
        'cliente': cliente,
        'form_plano': form_plano,
        'formset_refeicoes': formset_refeicoes,
        'is_edicao': plano_existente is not None
    }
    return render(request, 'core/criar_plano_alimentar.html', context)


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
            chave = normalizar_nome_refeicao(refeicao.nome)
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
            opcoes_objetivos = [{'value': key, 'label': label} for key, label in ClienteProfileUpdateForm.OBJETIVO_CHOICES]
            objetivos_selecionados = [obj.strip() for obj in cliente_profile.objetivos.split(',')] if cliente_profile.objetivos else []
            data = {
                'peso': cliente_profile.peso, 'altura': cliente_profile.altura,
                'idade': cliente_profile.idade, 'objetivos_selecionados': objetivos_selecionados, 
                'opcoes_objetivos': opcoes_objetivos, 'foto_url': cliente_profile.foto_perfil.url if cliente_profile.foto_perfil else None
            }
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
    if especialidade_id: nutricionistas = nutricionistas.filter(especialidades__id=especialidade_id)
    nome_busca = request.GET.get('nome')
    if nome_busca: nutricionistas = nutricionistas.filter(Q(usuario__first_name__icontains=nome_busca) | Q(usuario__last_name__icontains=nome_busca) | Q(usuario__username__icontains=nome_busca))
    context = { 'nutricionistas': nutricionistas, 'especialidades': especialidades, 'filtro_atual': int(especialidade_id) if especialidade_id else None, 'busca_atual': nome_busca }
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
                consulta = form.save(commit=False)
                consulta.cliente = cliente
                consulta.nutricionista = nutricionista
                consulta.data_horario = form.cleaned_data['data_horario_selecionado']
                
                consulta.duracao = nutricionista.duracao_consulta
                
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

        inicio_str = horarios_dia['inicio']
        fim_str = horarios_dia['fim']
        
        duracao_slot = nutri.duracao_consulta 
        
        hora_inicio = datetime.strptime(inicio_str, '%H:%M').time()
        hora_fim = datetime.strptime(fim_str, '%H:%M').time()

        consultas_marcadas = Consulta.objects.filter(
            nutricionista=nutri,
            data_horario__date=data_selecionada,
            status=Consulta.StatusChoices.CONFIRMADO
        )
        
        intervalos_ocupados = []
        tz = timezone.get_default_timezone()
        
        for consulta in consultas_marcadas:
            inicio_ocupado = consulta.data_horario
            if timezone.is_naive(inicio_ocupado):
                inicio_ocupado = timezone.make_aware(inicio_ocupado, tz)
            
            duracao_real = getattr(consulta, 'duracao', None)
            if not duracao_real: 
                duracao_real = nutri.duracao_consulta
                
            fim_ocupado = inicio_ocupado + timedelta(minutes=duracao_real)
            intervalos_ocupados.append((inicio_ocupado, fim_ocupado))

        horarios_disponiveis = []
        
        start_dt = timezone.make_aware(datetime.combine(data_selecionada, hora_inicio), tz)
        end_dt = timezone.make_aware(datetime.combine(data_selecionada, hora_fim), tz)
        
        current_slot = start_dt
        agora = timezone.now()

        while current_slot < end_dt:
            slot_finish = current_slot + timedelta(minutes=duracao_slot)
            if slot_finish > end_dt:
                break

            is_ocupado = False
            for (occ_start, occ_end) in intervalos_ocupados:
                if current_slot < occ_end and slot_finish > occ_start:
                    is_ocupado = True
                    break
            
            if not is_ocupado and current_slot > agora:
                horarios_disponiveis.append({
                    'display': current_slot.strftime('%H:%M'),
                    'valor_iso': current_slot.isoformat()
                })
            
            current_slot += timedelta(minutes=duracao_slot)

        return JsonResponse({'horarios': horarios_disponiveis})

    except Nutricionista.DoesNotExist:
        return JsonResponse({'error': 'Nutricionista não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def planos_alimentares_cliente(request):
    return redirect('dashboard_cliente')

@login_required
def cancelar_consulta(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id, cliente__usuario=request.user)
    consulta.status = Consulta.StatusChoices.CANCELADO
    consulta.save()
    return redirect('consultas_cliente')

@login_required
def plano_por_nutricionista(request, nutri_id):
    try:
        cliente = request.user.perfil_cliente
    except Cliente.DoesNotExist:
        return redirect('cadastro_cliente_perfil')
    
    nutricionista = get_object_or_404(Nutricionista, id=nutri_id)
    
    plano_atual = PlanoAlimentar.objects.filter(
        cliente=cliente, 
        nutricionista=nutricionista
    ).order_by('-data_criacao').first()
    
    refeicoes = []
    if plano_atual:
        refeicoes = plano_atual.refeicoes.all().order_by('id') 
        
    form_update = ClienteProfileUpdateForm(instance=cliente)
    
    context = { 
        'plano_atual': plano_atual, 
        'refeicoes': refeicoes, 
        'form_update': form_update, 
        'nutricionista_filtro': nutricionista.usuario.get_full_name() 
    }
    
    return render(request, 'core/planos_alimentares_cliente.html', context)