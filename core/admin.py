from django.contrib import admin
from .models import (
    User, Especialidade, Nutricionista, Cliente, 
    Consulta, PlanoAlimentar, Refeicao
)

class RefeicaoInline(admin.StackedInline):
    model = Refeicao
    extra = 6 
    min_num = 1   
    
    
    fieldsets = (
        (None, {
            'fields': ('nome', 'alimentos', 'quantidades', 'calorias'),
            'classes': ('collapse',), 
        }),
    )


class PlanoAlimentarAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nutricionista', 'data_criacao')
    list_filter = ('nutricionista', 'data_criacao')
    search_fields = ('cliente__usuario__first_name', 'cliente__usuario__last_name')
    

    inlines = [RefeicaoInline]


admin.site.register(User)
admin.site.register(Especialidade)
admin.site.register(Nutricionista)
admin.site.register(Cliente)
admin.site.register(Consulta)


try:
    admin.site.unregister(PlanoAlimentar)
except admin.sites.NotRegistered:
    pass


admin.site.register(PlanoAlimentar, PlanoAlimentarAdmin)


admin.site.register(Refeicao)