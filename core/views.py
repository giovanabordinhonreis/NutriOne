from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomAuthenticationForm

def login_usuario(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard') 
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login.html', {'form': form})

def dashboard(request):
    return render(request, 'dashboard.html')