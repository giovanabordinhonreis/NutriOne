from django.db import models
from django.contrib.auth.models import AbstractUser

# Defina um caminho para salvar as fotos de perfil
def user_directory_path(instance, filename):
    # O arquivo será salvo em MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.usuario.id}/profile_pics/{filename}'

class User(AbstractUser):
    class UserType(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente'
        NUTRICIONISTA = 'NUTRICIONISTA', 'Nutricionista'
        ADMIN = 'ADMIN', 'Admin'

    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15)
    user_type = models.CharField(max_length=20, choices=UserType.choices, default=UserType.CLIENTE)

class Especialidade(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Nutricionista(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_nutricionista')
    especialidades = models.ManyToManyField(Especialidade)
    preco_consulta = models.DecimalField(max_digits=8, decimal_places=2, help_text="Preço por consulta")
    duracao_consulta = models.IntegerField(help_text="Duração da consulta em minutos")
    horarios_disponiveis = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

class Cliente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_cliente')
    peso = models.FloatField(null=True, blank=True)
    altura = models.FloatField(null=True, blank=True, help_text="Altura em metros")
    idade = models.IntegerField(null=True, blank=True)
    objetivos = models.TextField(blank=True, null=True) # Mantido como TextField aqui
    
    # NOVO CAMPO ADICIONADO
    foto_perfil = models.ImageField(upload_to=user_directory_path, null=True, blank=True)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

# ... (restante dos modelos: Consulta, PlanoAlimentar, Refeicao) ...
class Consulta(models.Model):
    class ModalidadeChoices(models.TextChoices):
        PRESENCIAL = 'PRESENCIAL', 'Presencial'
        ONLINE = 'ONLINE', 'Online'

    class StatusChoices(models.TextChoices):
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        CONCLUIDO = 'CONCLUIDO', 'Concluído'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nutricionista = models.ForeignKey(Nutricionista, on_delete=models.CASCADE)
    data_horario = models.DateTimeField()
    modalidade = models.CharField(max_length=20, choices=ModalidadeChoices.choices)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.CONFIRMADO)

    def __str__(self):
        return f"Consulta de {self.cliente} com {self.nutricionista} em {self.data_horario.strftime('%d/%m/%Y %H:%M')}"

class PlanoAlimentar(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nutricionista = models.ForeignKey(Nutricionista, on_delete=models.CASCADE)
    data_criacao = models.DateField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Plano para {self.cliente} criado em {self.data_criacao.strftime('%d/%m/%Y')}"

class Refeicao(models.Model):
    plano_alimentar = models.ForeignKey(PlanoAlimentar, on_delete=models.CASCADE, related_name='refeicoes')
    nome = models.CharField(max_length=100)
    alimentos = models.TextField()
    quantidades = models.CharField(max_length=255)
    calorias = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.plano_alimentar}"