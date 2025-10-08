from django.contrib.auth.forms import AuthenticationForm

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