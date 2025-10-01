from django.contrib import admin
from .models import User, Especialidade, Nutricionista, Cliente, Consulta, PlanoAlimentar, Refeicao

admin.site.register(User)
admin.site.register(Especialidade)
admin.site.register(Nutricionista)
admin.site.register(Cliente)
admin.site.register(Consulta)
admin.site.register(PlanoAlimentar)
admin.site.register(Refeicao)