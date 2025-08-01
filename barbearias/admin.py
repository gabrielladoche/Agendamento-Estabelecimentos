from django.contrib import admin
from .models import Barbearia, Servico, Profissional, HorarioFuncionamento

@admin.register(Barbearia)
class BarbeariaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'ativa', 'usuario', 'criada_em']
    list_filter = ['ativa', 'criada_em']
    search_fields = ['nome', 'telefone']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'barbearia', 'preco', 'duracao_minutos', 'ativo']
    list_filter = ['barbearia', 'ativo']
    search_fields = ['nome', 'barbearia__nome']

@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ['nome', 'barbearia', 'ativo', 'criado_em']
    list_filter = ['barbearia', 'ativo']
    search_fields = ['nome', 'barbearia__nome']

@admin.register(HorarioFuncionamento)
class HorarioFuncionamentoAdmin(admin.ModelAdmin):
    list_display = ['barbearia', 'dia_semana', 'abertura', 'fechamento', 'fechado']
    list_filter = ['barbearia', 'dia_semana', 'fechado']
    search_fields = ['barbearia__nome']