from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Nutricionista, Especialidade, Cliente, Consulta

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
        self.fields['password1'].help_text = None
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


class ClienteProfileForm(forms.ModelForm):
    OBJETIVO_CHOICES = [
        ('', 'Selecione seu principal objetivo'),
        ('EMAGRECIMENTO', 'Emagrecimento'),
        ('GANHO_MASSA', 'Ganho de Massa Muscular'),
        ('REEDUCACAO_ALIMENTAR', 'Reeducação Alimentar'),
        ('NUTRICAO_ESPORTIVA', 'Nutrição Esportiva'),
        ('MELHORAR_SAUDE', 'Melhorar a Saúde/Disposição'),
        ('OUTRO', 'Outro'),
    ]

    objetivos = forms.ChoiceField(
        choices=OBJETIVO_CHOICES,
        label="Objetivos", 
        widget=forms.Select(attrs={'class': 'form-select', 'style': 'border-radius: 24px; padding: 12px;'}) 
    )

    class Meta:
        model = Cliente
        fields = ['foto_perfil', 'peso', 'altura', 'idade', 'objetivos']
        labels = {
            'foto_perfil': 'Foto de Perfil (Opcional)', 
            'peso': 'Peso (kg)',
            'altura': 'Altura (m)',
            'idade': 'Idade',
            'objetivos': 'Objetivos', 
        }
        widgets = {
            'foto_perfil': forms.ClearableFileInput(attrs={'class': 'form-control', 'style': 'border-radius: 24px; padding: 12px;'}),
            'peso': forms.NumberInput(attrs={'placeholder': '75,5', 'style': 'border-radius: 24px; padding: 12px;'}),
            'altura': forms.NumberInput(attrs={'placeholder': '1.78', 'style': 'border-radius: 24px; padding: 12px;'}),
            'idade': forms.NumberInput(attrs={'placeholder': '30', 'style': 'border-radius: 24px; padding: 12px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ClienteProfileUpdateForm(forms.ModelForm):
    OBJETIVO_CHOICES = ClienteProfileForm.OBJETIVO_CHOICES 
    objetivos = forms.ChoiceField( choices=OBJETIVO_CHOICES, label="Objetivos", widget=forms.Select(attrs={'class': 'form-select'}) )
    foto_perfil = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = Cliente; fields = ['foto_perfil', 'peso', 'altura', 'idade', 'objetivos'] 
        labels = { 'foto_perfil': 'Foto de Perfil', 'peso': 'Peso (kg)', 'altura': 'Altura (m)', 'idade': 'Idade', }
        widgets = { 'peso': forms.NumberInput(attrs={'class': 'form-control'}), 'altura': forms.NumberInput(attrs={'class': 'form-control'}), 'idade': forms.NumberInput(attrs={'class': 'form-control'}), }

class ConsultaForm(forms.ModelForm):
    modalidade = forms.ChoiceField( choices=Consulta.ModalidadeChoices.choices, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}), label="Modalidade" )
    data_horario_selecionado = forms.DateTimeField( widget=forms.HiddenInput(), required=True )
    class Meta:
        model = Consulta
        fields = ['modalidade', 'data_horario_selecionado']