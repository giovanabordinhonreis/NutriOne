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
    NutricionistaProfileUpdateForm, 
    PlanoAlimentarForm, RefeicaoFormSet 
)
from .models import (
    Nutricionista, Cliente, User, Consulta, 
    PlanoAlimentar, Refeicao, Especialidade
)


def normalizar_nome_refeicao(nome):
    if not nome: return ""
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
                if cd.get(f'{dia}_ativo'):
                    horarios[dia] = { 'inicio': cd[f'{dia}_inicio'].strftime('%H:%M') if cd.get(f'{dia}_inicio') else None, 'fim': cd[f'{dia}_fim'].strftime('%H:%M') if cd.get(f'{dia}_fim') else None }
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
    try:
        nutri = request.user.perfil_nutricionista
    except Nutricionista.DoesNotExist:
        return redirect('cadastro_nutricionista')
    hoje = timezone.now().date()
    consultas_hoje = Consulta.objects.filter(
        nutricionista=nutri, data_horario__date=hoje,
        status=Consulta.StatusChoices.CONFIRMADO
    ).order_by('data_horario')
    form_update = NutricionistaProfileUpdateForm(instance=nutri)
    context = { 'nutricionista': nutri, 'consultas_hoje': consultas_hoje, 'form_update': form_update, 'data_hoje': hoje }
    return render(request, 'core/dashboard_nutricionista.html', context)

@login_required
def perfil_nutricionista_ajax(request):
    nutri_profile = get_object_or_404(Nutricionista, usuario=request.user)
    if request.method == 'POST':
        form = NutricionistaProfileUpdateForm(request.POST, request.FILES, instance=nutri_profile)
        if form.is_valid():
            cd = form.cleaned_data; perfil_salvo = form.save(commit=False)
            horarios = {}
            dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado']
            for dia in dias_semana:
                if cd.get(f'{dia}_ativo'):
                    horarios[dia] = { 'inicio': cd[f'{dia}_inicio'].strftime('%H:%M') if cd.get(f'{dia}_inicio') else None, 'fim': cd[f'{dia}_fim'].strftime('%H:%M') if cd.get(f'{dia}_fim') else None, }
            perfil_salvo.horarios_disponiveis = horarios
            perfil_salvo.save(); form.save_m2m() 
            foto_url = perfil_salvo.foto_perfil.url if perfil_salvo.foto_perfil else None
            return JsonResponse({'success': True, 'foto_url': foto_url})
        else: return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    elif request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = NutricionistaProfileUpdateForm(instance=nutri_profile)
        data = form.initial 
        data['foto_url'] = nutri_profile.foto_perfil.url if nutri_profile.foto_perfil else None
        data['especialidades'] = list(nutri_profile.especialidades.values_list('id', flat=True))
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
@transaction.atomic 
def criar_plano_alimentar(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    nutricionista = request.user.perfil_nutricionista
    plano = PlanoAlimentar(cliente=cliente, nutricionista=nutricionista)
    if request.method == 'POST':
        form_plano = PlanoAlimentarForm(request.POST, instance=plano)
        formset_refeicoes = RefeicaoFormSet(request.POST, instance=plano)
        if form_plano.is_valid() and formset_refeicoes.is_valid():
            plano_salvo = form_plano.save()
            formset_refeicoes.instance = plano_salvo
            formset_refeicoes.save()
            return redirect('clientes_nutri')
    else: 
        form_plano = PlanoAlimentarForm(instance=plano)
        formset_refeicoes = RefeicaoFormSet(instance=plano)
    form_update = NutricionistaProfileUpdateForm(instance=nutricionista)
    refeicoes_labels = [ "Café da Manhã", "Lanche da Manhã", "Almoço", "Lanche da Tarde", "Jantar", "Ceia" ]
    context = { 'cliente': cliente, 'form_plano': form_plano, 'formset_refeicoes': formset_refeicoes, 'form_update': form_update, 'refeicoes_labels': refeicoes_labels }
    return render(request, 'core/criar_plano_alimentar.html', context)


@login_required
def cadastro_cliente_perfil(request):
    if request.method == 'POST':
        # Importante: request.FILES para salvar a foto
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
    
    nome_busca = request.GET.get('nome')
    if nome_busca:
        nutricionistas = nutricionistas.filter(
            Q(usuario__first_name__icontains=nome_busca) | 
            Q(usuario__last_name__icontains=nome_busca) |
            Q(usuario__username__icontains=nome_busca)
        )

    context = { 
        'nutricionistas': nutricionistas, 
        'especialidades': especialidades, 
        'filtro_atual': int(especialidade_id) if especialidade_id else None,
        'busca_atual': nome_busca 
    }
    return render(request, 'core/encontrar_nutricionista.html', context)

@login_required
def agendar_consulta(request, nutri_id):
    nutricionista = get_object_or_404(Nutricionista, id=nutri_id, is_approved=True)
    cliente = request.user.perfil_cliente
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            try:
                consulta = form.save(commit=False); consulta.cliente = cliente; consulta.nutricionista = nutricionista
                consulta.data_horario = form.cleaned_data['data_horario_selecionado']
                consulta.status = Consulta.StatusChoices.CONFIRMADO; consulta.save() 
                return redirect('consultas_cliente')
            except IntegrityError:
                form.add_error(None, "Desculpe, este horário acabou de ser agendado ou já está ocupado.")
    else: form = ConsultaForm()
    context = { 'nutricionista': nutricionista, 'form': form, 'today': timezone.now() }
    return render(request, 'core/agendar_consulta.html', context)

@login_required
def api_horarios_disponiveis(request):
    nutricionista_id = request.GET.get('nutri_id'); data_selecionada_str = request.GET.get('data') 
    if not nutricionista_id or not data_selecionada_str:
        return JsonResponse({'error': 'Faltando parâmetros'}, status=400)
    try:
        nutri = Nutricionista.objects.get(id=nutricionista_id)
        data_selecionada = datetime.strptime(data_selecionada_str, '%Y-%m-%d').date()
        dia_semana_num = data_selecionada.weekday(); dias_map = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']; dia_semana_str = dias_map[dia_semana_num]
        
        horarios_dia = nutri.horarios_disponiveis.get(dia_semana_str)
        if not horarios_dia or not horarios_dia.get('inicio') or not horarios_dia.get('fim'):
            return JsonResponse({'horarios': []}) 
            
        inicio_str = horarios_dia['inicio']; fim_str = horarios_dia['fim']; duracao = nutri.duracao_consulta
        hora_inicio = datetime.strptime(inicio_str, '%H:%M').time(); hora_fim = datetime.strptime(fim_str, '%H:%M').time()
        
        consultas_marcadas = Consulta.objects.filter( 
            nutricionista=nutri, 
            data_horario__date=data_selecionada, 
            status=Consulta.StatusChoices.CONFIRMADO 
        ).values_list('data_horario', flat=True)
        
        horarios_ocupados = set()
        for data_ocupada in consultas_marcadas:
            horario_local = timezone.localtime(data_ocupada).time()
            horarios_ocupados.add(horario_local)

        horarios_disponiveis = []; hora_atual = datetime.combine(data_selecionada, hora_inicio); hora_fim_dt = datetime.combine(data_selecionada, hora_fim)
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
    plano_atual = PlanoAlimentar.objects.filter( cliente=cliente ).order_by('-data_criacao').first()
    refeicoes = []
    if plano_atual:
        refeicoes = plano_atual.refeicoes.all().order_by('id') 
    form_update = ClienteProfileUpdateForm(instance=cliente)
    context = { 'plano_atual': plano_atual, 'refeicoes': refeicoes, 'form_update': form_update, }
    return render(request, 'core/planos_alimentares_cliente.html', context)

@login_required
def plano_por_nutricionista(request, nutri_id):
    try:
        cliente = request.user.perfil_cliente
        nutricionista = get_object_or_404(Nutricionista, id=nutri_id)
    except Cliente.DoesNotExist:
        return redirect('cadastro_cliente_perfil')
    plano_atual = PlanoAlimentar.objects.filter( cliente=cliente, nutricionista=nutricionista ).order_by('-data_criacao').first()
    refeicoes = []
    if plano_atual:
        refeicoes = plano_atual.refeicoes.all().order_by('id') 
    form_update = ClienteProfileUpdateForm(instance=cliente)
    context = { 'plano_atual': plano_atual, 'refeicoes': refeicoes, 'form_update': form_update, 'nutricionista_filtro': nutricionista.usuario.get_full_name() }
    return render(request, 'core/planos_alimentares_cliente.html', context)

@login_required
def cancelar_consulta(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id, cliente__usuario=request.user)
    consulta.status = Consulta.StatusChoices.CANCELADO
    consulta.save()
    return redirect('consultas_cliente')