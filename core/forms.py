from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Nutricionista, Especialidade, Cliente, Consulta, PlanoAlimentar, Refeicao
import json



class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email', 'telefone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Nome'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Sobrenome'})
        self.fields['email'].widget.attrs.update({'placeholder': 'E-mail'})
        self.fields['telefone'].widget.attrs.update({'placeholder': 'Telefone'})
        

        if 'password1' in self.fields:
            self.fields['password1'].help_text = None
        if 'password2' in self.fields:
            self.fields['password2'].help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Digite seu e-mail'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Digite sua senha'}
        )
        self.fields['username'].label = ""
        self.fields['password'].label = ""



class ClienteProfileForm(forms.ModelForm):
    OBJETIVO_CHOICES = [
        ('EMAGRECIMENTO', 'Emagrecimento'),
        ('GANHO_MASSA', 'Ganho de Massa Muscular'),
        ('REEDUCACAO_ALIMENTAR', 'Reeducação Alimentar'),
        ('NUTRICAO_ESPORTIVA', 'Nutrição Esportiva'),
        ('MELHORAR_SAUDE', 'Melhorar a Saúde/Disposição'),
        ('OUTRO', 'Outro'),
    ]


    objetivos = forms.MultipleChoiceField(
        choices=OBJETIVO_CHOICES,
        label="Objetivos",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    

    foto_perfil = forms.ImageField(
        label="Foto de Perfil (Opcional)",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Cliente
        fields = ['foto_perfil', 'peso', 'altura', 'idade', 'objetivos']
        labels = {
            'peso': 'Peso (kg)',
            'altura': 'Altura (m)',
            'idade': 'Idade',
        }
        widgets = {
            'peso': forms.NumberInput(attrs={'placeholder': '75,5', 'class': 'form-control'}),
            'altura': forms.NumberInput(attrs={'placeholder': '1.78', 'class': 'form-control'}),
            'idade': forms.NumberInput(attrs={'placeholder': '30', 'class': 'form-control'}),
        }
    
    def clean_objetivos(self):

        objetivos_lista = self.cleaned_data.get('objetivos')
        if objetivos_lista:
            return ", ".join(objetivos_lista)
        return ""

class ClienteProfileUpdateForm(forms.ModelForm):
    OBJETIVO_CHOICES = ClienteProfileForm.OBJETIVO_CHOICES 
    
    objetivos = forms.MultipleChoiceField(
        choices=OBJETIVO_CHOICES,
        label="Objetivos",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    foto_perfil = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Cliente; fields = ['foto_perfil', 'peso', 'altura', 'idade', 'objetivos'] 
        labels = { 'foto_perfil': 'Foto de Perfil', 'peso': 'Peso (kg)', 'altura': 'Altura (m)', 'idade': 'Idade', }
        widgets = { 'peso': forms.NumberInput(attrs={'class': 'form-control'}), 'altura': forms.NumberInput(attrs={'class': 'form-control'}), 'idade': forms.NumberInput(attrs={'class': 'form-control'}), }

    def clean_objetivos(self):
        objetivos_lista = self.cleaned_data.get('objetivos')
        if objetivos_lista:
            return ", ".join(objetivos_lista)
        return ""

class ConsultaForm(forms.ModelForm):
    modalidade = forms.ChoiceField(
        choices=Consulta.ModalidadeChoices.choices,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Modalidade"
    )
    data_horario_selecionado = forms.DateTimeField(
        widget=forms.HiddenInput(),
        required=True
    )

    class Meta:
        model = Consulta
        fields = ['modalidade'] 



class NutricionistaProfileForm(forms.ModelForm):
    especialidades = forms.ModelMultipleChoiceField(
        queryset=Especialidade.objects.all(),
        label="Especialidades",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    class Meta:
        model = Nutricionista
        fields = ['especialidades', 'preco_consulta', 'duracao_consulta']
        widgets = { 'preco_consulta': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120,00'}), 'duracao_consulta': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '60'}), }
        labels = { 'preco_consulta': 'Preço por Consulta (R$)', 'duracao_consulta': 'Duração da Consulta (minutos)', }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dias_semana = [ ('segunda', 'Segunda-feira'), ('terca', 'Terça-feira'), ('quarta', 'Quarta-feira'), ('quinta', 'Quinta-feira'), ('sexta', 'Sexta-feira'), ('sabado', 'Sábado'), ]
        for dia_key, dia_label in self.dias_semana:
            self.fields[f'{dia_key}_ativo'] = forms.BooleanField( required=False, label=dia_label, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}) )
            self.fields[f'{dia_key}_inicio'] = forms.TimeField( required=False, widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm', 'value': '08:00'}) )
            self.fields[f'{dia_key}_fim'] = forms.TimeField( required=False, widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm', 'value': '18:00'}) )

class NutricionistaProfileUpdateForm(NutricionistaProfileForm):
    foto_perfil = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    especialidades = forms.ModelMultipleChoiceField(
        queryset=Especialidade.objects.all(),
        label="Especialidades",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    class Meta(NutricionistaProfileForm.Meta):
        fields = ['foto_perfil'] + NutricionistaProfileForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.horarios_disponiveis:
            horarios = self.instance.horarios_disponiveis
            if isinstance(horarios, str):
                try: horarios = json.loads(horarios)
                except json.JSONDecodeError: horarios = {}
            for dia_key in ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado']:
                if dia_key in horarios and horarios[dia_key].get('inicio'):
                    self.initial[f'{dia_key}_ativo'] = True
                    self.initial[f'{dia_key}_inicio'] = horarios[dia_key].get('inicio')
                    self.initial[f'{dia_key}_fim'] = horarios[dia_key].get('fim')
                else:
                    self.initial[f'{dia_key}_ativo'] = False


class PlanoAlimentarForm(forms.ModelForm):
    class Meta:
        model = PlanoAlimentar
        fields = ['observacoes']
        widgets = { 'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: Evitar glúten, beber 2L de água por dia...'}), }
        labels = { 'observacoes': 'Observações Gerais do Plano', }

class RefeicaoForm(forms.ModelForm):
    class Meta:
        model = Refeicao
        fields = ['nome', 'alimentos', 'quantidades', 'calorias']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: Café da Manhã'}),
            'alimentos': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Ex: 1x Banana, 20g Aveia'}),
            'quantidades': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: 1 unidade, 2 colheres'}),
            'calorias': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: 350'}),
        }
        labels = { 'nome': 'Nome da Refeição', 'alimentos': 'Alimentos', 'quantidades': 'Quantidades', 'calorias': 'Calorias (kcal)', }

RefeicaoFormSet = forms.inlineformset_factory(
    PlanoAlimentar, Refeicao, form=RefeicaoForm, extra=6, min_num=1, can_delete=True
)