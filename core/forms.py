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
    def save(self, commit=True):
        user = super().save(commit=False); user.username = self.cleaned_data['email']
        if commit: user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update( {'class': 'form-control', 'placeholder': 'Digite seu e-mail'} )
        self.fields['password'].widget.attrs.update( {'class': 'form-control', 'placeholder': 'Digite sua senha'} )
        self.fields['username'].label = ""; self.fields['password'].label = ""

class NutricionistaProfileForm(forms.ModelForm):
    
    especialidades = forms.ModelChoiceField( queryset=Especialidade.objects.all(), label="Especialidades", empty_label="Selecione sua principal especialidade", widget=forms.Select(attrs={'class': 'form-select'}) )
    class Meta:
        model = Nutricionista
        fields = ['especialidades', 'preco_consulta', 'duracao_consulta']
        widgets = { 'preco_consulta': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120,00'}), 'duracao_consulta': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '60'}), }
        labels = { 'preco_consulta': 'Preço por Consulta (R$)', 'duracao_consulta': 'Duração da Consulta (minutos)', }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dias_semana = [ ('segunda', 'Segunda-feira'), ('terca', 'Terça-feira'), ('quarta', 'Quarta-feira'), ('quinta', 'Quinta-feira'), ('sexta', 'Sexta-feira'), ('sabado', 'Sábado'), ]
        for dia_key, dia_label in dias_semana:
            self.fields[f'{dia_key}_ativo'] = forms.BooleanField(
                required=False, 
                label=dia_label,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )
            self.fields[f'{dia_key}_inicio'] = forms.TimeField(
                required=False,
                widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm', 'value': '08:00'})
            )
            self.fields[f'{dia_key}_fim'] = forms.TimeField(
                required=False,
                widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm', 'value': '18:00'})
            )

class ClienteProfileForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['peso', 'altura', 'idade', 'objetivos']
        widgets = {
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 70,5'}),
            'altura': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1,75'}),
            'idade': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 30'}),
            'objetivos': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ex: Emagrecimento, ganhar massa...', 'rows': 4}),
        }
        labels = {
            'peso': 'Peso (kg)',
            'altura': 'Altura (m)',
            'idade': 'Idade',
            'objetivos': 'Quais são seus objetivos?',
        }