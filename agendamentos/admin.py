from django.contrib import admin
from .models import Agendamento

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['nome_cliente', 'telefone_cliente', 'servico', 'profissional', 'barbearia', 'data_hora', 'status']
    list_filter = ['barbearia', 'status', 'data_hora', 'servico']
    search_fields = ['nome_cliente', 'telefone_cliente']
    date_hierarchy = 'data_hora'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            barbearia = request.user.barbearia
            return qs.filter(barbearia=barbearia)
        except:
            return qs.none()
