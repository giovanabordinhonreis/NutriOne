from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Especialidade, Nutricionista, Cliente, Consulta, PlanoAlimentar, Refeicao

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Extras', {'fields': ('user_type', 'telefone')}),
    )

@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Nutricionista)
class NutricionistaAdmin(admin.ModelAdmin):
    list_display = ('get_nome_completo', 'get_email', 'preco_consulta', 'is_approved')
    list_filter = ('is_approved', 'especialidades')
    search_fields = ('usuario__first_name', 'usuario__email')
    
    filter_horizontal = ('especialidades',) 
    
    def get_nome_completo(self, obj):
        return obj.usuario.get_full_name()
    get_nome_completo.short_description = 'Nome'

    def get_email(self, obj):
        return obj.usuario.email
    get_email.short_description = 'E-mail'

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('get_nome', 'get_email', 'idade')
    search_fields = ('usuario__first_name', 'usuario__email')

    def get_nome(self, obj):
        return obj.usuario.get_full_name()
    get_nome.short_description = 'Nome'
    
    def get_email(self, obj):
        return obj.usuario.email
    get_email.short_description = 'E-mail'

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nutricionista', 'data_horario', 'status', 'duracao')
    list_filter = ('status', 'data_horario')
    date_hierarchy = 'data_horario'

class RefeicaoInline(admin.TabularInline):
    model = Refeicao
    extra = 1 
    min_num = 1

@admin.register(PlanoAlimentar)
class PlanoAlimentarAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nutricionista', 'data_criacao')
    list_filter = ('data_criacao',)
    search_fields = ('cliente__usuario__first_name',)
    
    inlines = [RefeicaoInline]
admin.site.register(Refeicao)