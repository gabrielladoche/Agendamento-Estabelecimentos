from django.urls import path
from . import views

app_name = 'barbearias'

urlpatterns = [
    # URLs públicas
    path('', views.redirect_to_default, name='redirect_to_default'),
    path('<slug:slug>/', views.mini_site, name='mini_site'),
    path('<slug:slug>/agendar/', views.agendar, name='agendar'),
    path('<slug:slug>/consultar/', views.consultar_agendamentos_local, name='consultar_agendamentos_local'),
    path('<slug:slug>/agendamentos/<int:agendamento_id>/cancelar/', views.cancelar_agendamento_cliente, name='cancelar_agendamento_cliente'),
    path('<slug:slug>/api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
    path('<slug:slug>/api/dias-fechados/', views.api_dias_fechados, name='api_dias_fechados'),
    
    # URLs administrativas (protegidas por login próprio)
    path('<slug:slug>/admin/login/', views.admin_login, name='admin_login'),
    path('<slug:slug>/admin/logout/', views.admin_logout, name='admin_logout'),
    path('<slug:slug>/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('<slug:slug>/admin/servicos/', views.admin_servicos_lista, name='admin_servicos_lista'),
    path('<slug:slug>/admin/servicos/criar/', views.admin_servico_criar, name='admin_servico_criar'),
    path('<slug:slug>/admin/servicos/<int:servico_id>/editar/', views.admin_servico_editar, name='admin_servico_editar'),
    path('<slug:slug>/admin/servicos/<int:servico_id>/deletar/', views.admin_servico_deletar, name='admin_servico_deletar'),
    path('<slug:slug>/admin/agendamentos/', views.admin_agendamentos_lista, name='admin_agendamentos_lista'),
    path('<slug:slug>/admin/agendamentos/<int:agendamento_id>/status/', views.admin_agendamento_atualizar_status, name='admin_agendamento_atualizar_status'),
    path('<slug:slug>/admin/profissionais/', views.admin_profissionais_lista, name='admin_profissionais_lista'),
    path('<slug:slug>/admin/profissionais/criar/', views.admin_profissional_criar, name='admin_profissional_criar'),
    # path('<slug:slug>/admin/profissionais/<int:profissional_id>/editar/', views.admin_profissional_editar, name='admin_profissional_editar'),
    # path('<slug:slug>/admin/profissionais/<int:profissional_id>/deletar/', views.admin_profissional_deletar, name='admin_profissional_deletar'),
    path('<slug:slug>/admin/profissionais/<int:profissional_id>/agenda/', views.admin_agenda_profissional, name='admin_agenda_profissional'),
    path('<slug:slug>/admin/horarios/', views.admin_horarios_funcionamento, name='admin_horarios_funcionamento'),
    path('<slug:slug>/admin/configuracoes/', views.admin_configuracoes, name='admin_configuracoes'),
]
