from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import Barbearia, Servico, Profissional, HorarioFuncionamento
from .forms import ServicoForm, ProfissionalForm, LoginBarbeiroForm, HorarioFuncionamentoForm, BarbeariaConfigForm
from django.contrib.auth import login, logout
from agendamentos.models import Agendamento
from agendamentos.forms import AgendamentoForm
from agendamentos.utils import enviar_notificacao_novo_agendamento
from django.utils import timezone
from datetime import datetime, timedelta

def redirect_to_default(request):
    """Redireciona para o estabelecimento padrão"""
    try:
        # Tenta usar o slug padrão configurado
        default_slug = getattr(settings, 'DEFAULT_BARBEARIA_SLUG', None)
        if default_slug:
            barbearia = Barbearia.objects.get(slug=default_slug, ativa=True)
            return redirect('barbearias:mini_site', slug=default_slug)
    except Barbearia.DoesNotExist:
        pass
    
    # Se não encontrar o padrão, pega o primeiro ativo
    try:
        primeira_barbearia = Barbearia.objects.filter(ativa=True).first()
        if primeira_barbearia:
            return redirect('barbearias:mini_site', slug=primeira_barbearia.slug)
    except:
        pass
    
    # Se não houver nenhuma barbearia ativa, mostra página de erro
    return render(request, 'barbearias/no_barbearia.html', status=404)

def consultar_agendamentos_local(request, slug):
    """Consulta de agendamentos de uma barbearia específica"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    agendamentos = []
    telefone = None
    
    if request.method == 'POST':
        telefone = request.POST.get('telefone', '').strip()
        if telefone:
            agendamentos = Agendamento.objects.filter(
                barbearia=barbearia,  # Filtra apenas por esta barbearia
                telefone_cliente__icontains=telefone,
                data_hora__gte=timezone.now() - timedelta(days=30)
            ).order_by('-data_hora')
    elif request.method == 'GET' and request.GET.get('telefone'):
        # Para preservar telefone após redirecionamento
        telefone = request.GET.get('telefone', '').strip()
        if telefone:
            agendamentos = Agendamento.objects.filter(
                barbearia=barbearia,
                telefone_cliente__icontains=telefone,
                data_hora__gte=timezone.now() - timedelta(days=30)
            ).order_by('-data_hora')
    
    context = {
        'barbearia': barbearia,
        'agendamentos': agendamentos,
        'telefone': telefone,
    }
    return render(request, 'barbearias/consultar_agendamentos.html', context)

@login_required
def painel_admin_default(request):
    """Painel administrativo da barbearia padrão"""
    barbearia = get_default_barbearia()
    if not barbearia:
        return render(request, 'barbearias/no_barbearia.html')
    
    # Verifica se o usuário tem permissão para esta barbearia
    if barbearia.usuario != request.user:
        messages.error(request, 'Você não tem permissão para acessar esta barbearia.')
        return redirect('admin:index')
    
    # Estatísticas básicas
    hoje = timezone.now().date()
    agendamentos_hoje = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__date=hoje
    ).count()
    
    agendamentos_pendentes = Agendamento.objects.filter(
        barbearia=barbearia,
        status='agendado',
        data_hora__gte=timezone.now()
    ).count()
    
    # Próximos agendamentos
    proximos_agendamentos = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__gte=timezone.now(),
        status__in=['agendado', 'confirmado']
    )[:10]
    
    context = {
        'barbearia': barbearia,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_pendentes': agendamentos_pendentes,
        'proximos_agendamentos': proximos_agendamentos,
    }
    return render(request, 'barbearias/painel_admin.html', context)

def mini_site(request, slug):
    """Mini site público da barbearia"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    servicos = barbearia.servicos.filter(ativo=True)
    profissionais = barbearia.profissionais.filter(ativo=True)
    
    context = {
        'barbearia': barbearia,
        'servicos': servicos,
        'profissionais': profissionais,
    }
    return render(request, 'barbearias/mini_site.html', context)

def agendar(request, slug):
    """Formulário de agendamento público"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    if request.method == 'POST':
        form = AgendamentoForm(request.POST, barbearia=barbearia)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.barbearia = barbearia
            try:
                agendamento.save()
                
                # Enviar notificação para o estabelecimento
                try:
                    resultado = enviar_notificacao_novo_agendamento(agendamento)
                    if resultado:
                        print(f"✅ Notificação enviada com sucesso para agendamento #{agendamento.id}")
                        messages.success(request, f'Agendamento realizado com sucesso! Uma notificação foi enviada para {barbearia.nome}.')
                    else:
                        print(f"❌ Falha ao enviar notificação para agendamento #{agendamento.id}")
                        if not barbearia.email_notificacoes:
                            messages.success(request, 'Agendamento realizado com sucesso!')
                        else:
                            messages.warning(request, 'Agendamento realizado, mas houve problema ao enviar notificação ao estabelecimento.')
                except Exception as e:
                    print(f"🚨 Erro ao enviar notificação: {str(e)}")
                    messages.warning(request, 'Agendamento realizado, mas houve problema ao enviar notificação ao estabelecimento.')
                
                return redirect('barbearias:mini_site', slug=slug)
            except Exception as e:
                messages.error(request, f'Erro ao realizar agendamento: {str(e)}')
    else:
        form = AgendamentoForm(barbearia=barbearia)
    
    context = {
        'barbearia': barbearia,
        'form': form,
    }
    return render(request, 'barbearias/agendar.html', context)

@login_required
def painel_admin(request, slug):
    """Painel administrativo da barbearia"""
    try:
        barbearia = get_object_or_404(Barbearia, slug=slug, usuario=request.user)
    except:
        messages.error(request, 'Você não tem permissão para acessar esta barbearia.')
        return redirect('admin:index')
    
    # Estatísticas básicas
    hoje = timezone.now().date()
    agendamentos_hoje = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__date=hoje
    ).count()
    
    agendamentos_pendentes = Agendamento.objects.filter(
        barbearia=barbearia,
        status='agendado',
        data_hora__gte=timezone.now()
    ).count()
    
    # Próximos agendamentos
    proximos_agendamentos = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__gte=timezone.now(),
        status__in=['agendado', 'confirmado']
    )[:10]
    
    context = {
        'barbearia': barbearia,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_pendentes': agendamentos_pendentes,
        'proximos_agendamentos': proximos_agendamentos,
    }
    return render(request, 'barbearias/painel_admin.html', context)

def consultar_agendamentos(request):
    """Consulta de agendamentos por telefone"""
    agendamentos = []
    telefone = None
    
    if request.method == 'POST':
        telefone = request.POST.get('telefone', '').strip()
        if telefone:
            agendamentos = Agendamento.objects.filter(
                telefone_cliente__icontains=telefone,
                data_hora__gte=timezone.now() - timedelta(days=30)  # Últimos 30 dias
            ).order_by('-data_hora')
    
    context = {
        'agendamentos': agendamentos,
        'telefone': telefone,
    }
    return render(request, 'barbearias/consultar_agendamentos.html', context)

# ===== VIEWS ADMINISTRATIVAS =====

def barbeiro_required(view_func):
    """Decorator que verifica se o barbeiro está logado e tem acesso à barbearia"""
    def _wrapped_view(request, slug, *args, **kwargs):
        # Verificar se está logado
        if not request.user.is_authenticated:
            messages.info(request, 'Faça login para acessar a área administrativa.')
            return redirect('barbearias:admin_login', slug=slug)
        
        # Verificar se tem acesso à barbearia
        try:
            barbearia = Barbearia.objects.get(slug=slug, ativa=True)
            if barbearia.usuario != request.user:
                messages.error(request, 'Você não tem permissão para acessar esta barbearia.')
                logout(request)
                return redirect('barbearias:admin_login', slug=slug)
        except Barbearia.DoesNotExist:
            messages.error(request, 'Barbearia não encontrada.')
            return redirect('barbearias:redirect_to_default')
        
        return view_func(request, slug, *args, **kwargs)
    return _wrapped_view

def admin_login(request, slug):
    """Login específico para barbeiros"""
    # Verificar se a barbearia existe
    try:
        barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    except Barbearia.DoesNotExist:
        messages.error(request, 'Barbearia não encontrada.')
        return redirect('barbearias:redirect_to_default')
    
    # Se já está logado e tem acesso, redirecionar
    if request.user.is_authenticated:
        if barbearia.usuario == request.user:
            return redirect('barbearias:admin_dashboard', slug=slug)
        else:
            # Logado com usuário errado, fazer logout
            logout(request)
    
    if request.method == 'POST':
        form = LoginBarbeiroForm(request.POST, slug=slug, request=request)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
            return redirect('barbearias:admin_dashboard', slug=slug)
    else:
        form = LoginBarbeiroForm(slug=slug, request=request)
    
    context = {
        'form': form,
        'barbearia': barbearia,
    }
    return render(request, 'barbearias/admin/login.html', context)

def admin_logout(request, slug):
    """Logout para barbeiros"""
    logout(request)
    messages.success(request, 'Você saiu da área administrativa.')
    return redirect('barbearias:mini_site', slug=slug)

@barbeiro_required
def admin_dashboard(request, slug):
    """Dashboard administrativo da barbearia"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    
    # Estatísticas básicas
    hoje = timezone.now().date()
    agendamentos_hoje = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__date=hoje
    ).count()
    
    agendamentos_pendentes = Agendamento.objects.filter(
        barbearia=barbearia,
        status='agendado',
        data_hora__gte=timezone.now()
    ).count()
    
    total_servicos = barbearia.servicos.filter(ativo=True).count()
    total_profissionais = barbearia.profissionais.filter(ativo=True).count()
    
    # Próximos agendamentos
    proximos_agendamentos = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__gte=timezone.now(),
        status__in=['agendado', 'confirmado']
    )[:5]
    
    context = {
        'barbearia': barbearia,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_pendentes': agendamentos_pendentes,
        'total_servicos': total_servicos,
        'total_profissionais': total_profissionais,
        'proximos_agendamentos': proximos_agendamentos,
    }
    return render(request, 'barbearias/admin/dashboard.html', context)

@barbeiro_required
def admin_servicos_lista(request, slug):
    """Lista de serviços para administração"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    servicos = barbearia.servicos.all().order_by('nome')
    
    context = {
        'barbearia': barbearia,
        'servicos': servicos,
    }
    return render(request, 'barbearias/admin/servicos_lista.html', context)

@barbeiro_required
def admin_servico_criar(request, slug):
    """Criar novo serviço"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    
    if request.method == 'POST':
        form = ServicoForm(request.POST)
        if form.is_valid():
            servico = form.save(commit=False)
            servico.barbearia = barbearia
            servico.save()
            messages.success(request, 'Serviço criado com sucesso!')
            return redirect('barbearias:admin_servicos_lista', slug=slug)
    else:
        form = ServicoForm()
    
    context = {
        'barbearia': barbearia,
        'form': form,
        'titulo': 'Criar Serviço',
        'botao': 'Criar Serviço'
    }
    return render(request, 'barbearias/admin/servico_form.html', context)

@barbeiro_required
def admin_servico_editar(request, slug, servico_id):
    """Editar serviço existente"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    servico = get_object_or_404(Servico, id=servico_id, barbearia=barbearia)
    
    if request.method == 'POST':
        form = ServicoForm(request.POST, instance=servico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço atualizado com sucesso!')
            return redirect('barbearias:admin_servicos_lista', slug=slug)
    else:
        form = ServicoForm(instance=servico)
    
    context = {
        'barbearia': barbearia,
        'servico': servico,
        'form': form,
        'titulo': 'Editar Serviço',
        'botao': 'Salvar Alterações',
    }
    return render(request, 'barbearias/admin/servico_form.html', context)

@barbeiro_required
def admin_servico_deletar(request, slug, servico_id):
    """Deletar serviço"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    servico = get_object_or_404(Servico, id=servico_id, barbearia=barbearia)
    
    if request.method == 'POST':
        servico.delete()
        messages.success(request, 'Serviço deletado com sucesso!')
        return redirect('barbearias:admin_servicos_lista', slug=slug)
    
    context = {
        'barbearia': barbearia,
        'servico': servico,
    }
    return render(request, 'barbearias/admin/servico_deletar.html', context)

@barbeiro_required
def admin_agendamentos_lista(request, slug):
    """Lista de agendamentos da barbearia"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    
    # Filtros
    data_filtro = request.GET.get('data', '')
    status_filtro = request.GET.get('status', '')
    profissional_filtro = request.GET.get('profissional', '')
    
    # Query base
    agendamentos = Agendamento.objects.filter(barbearia=barbearia)
    
    # Aplicar filtros
    if data_filtro:
        try:
            from datetime import datetime
            data = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            agendamentos = agendamentos.filter(data_hora__date=data)
        except ValueError:
            pass
    
    if status_filtro:
        agendamentos = agendamentos.filter(status=status_filtro)
    
    if profissional_filtro:
        try:
            profissional_id = int(profissional_filtro)
            agendamentos = agendamentos.filter(profissional_id=profissional_id)
        except (ValueError, TypeError):
            pass
    
    # Se não houver filtro de data, mostrar apenas agendamentos dos próximos 30 dias
    if not data_filtro:
        from datetime import date, timedelta
        hoje = date.today()
        data_limite = hoje + timedelta(days=30)
        agendamentos = agendamentos.filter(
            data_hora__date__gte=hoje,
            data_hora__date__lte=data_limite
        )
    
    # Ordenar por data/hora
    agendamentos = agendamentos.order_by('data_hora')
    
    # Para os filtros no template
    profissionais = barbearia.profissionais.filter(ativo=True)
    status_choices = Agendamento.STATUS_CHOICES
    
    context = {
        'barbearia': barbearia,
        'agendamentos': agendamentos,
        'profissionais': profissionais,
        'status_choices': status_choices,
        'data_filtro': data_filtro,
        'status_filtro': status_filtro,
        'profissional_filtro': profissional_filtro,
    }
    return render(request, 'barbearias/admin/agendamentos_lista.html', context)

@barbeiro_required
def admin_agendamento_atualizar_status(request, slug, agendamento_id):
    """Atualizar status de um agendamento"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, barbearia=barbearia)
    
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        if novo_status in dict(Agendamento.STATUS_CHOICES):
            agendamento.status = novo_status
            agendamento.save()
            
            status_nome = dict(Agendamento.STATUS_CHOICES)[novo_status]
            messages.success(request, f'Agendamento de {agendamento.nome_cliente} atualizado para "{status_nome}".')
        else:
            messages.error(request, 'Status inválido.')
    
    return redirect('barbearias:admin_agendamentos_lista', slug=slug)

@barbeiro_required
def admin_profissionais_lista(request, slug):
    """Lista de profissionais para administração"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    profissionais = barbearia.profissionais.all().order_by('nome')
    
    context = {
        'barbearia': barbearia,
        'profissionais': profissionais,
    }
    return render(request, 'barbearias/admin/profissionais_lista.html', context)

@barbeiro_required
def admin_profissional_criar(request, slug):
    """Criar novo profissional"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    
    if request.method == 'POST':
        form = ProfissionalForm(request.POST)
        if form.is_valid():
            profissional = form.save(commit=False)
            profissional.barbearia = barbearia
            profissional.save()
            messages.success(request, 'Profissional criado com sucesso!')
            return redirect('barbearias:admin_profissionais_lista', slug=slug)
    else:
        form = ProfissionalForm()
    
    context = {
        'barbearia': barbearia,
        'form': form,
        'titulo': 'Criar Profissional',
        'botao': 'Criar Profissional'
    }
    return render(request, 'barbearias/admin/profissional_form.html', context)

@barbeiro_required
def admin_profissional_editar(request, slug, profissional_id):
    """Editar profissional existente"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    profissional = get_object_or_404(Profissional, id=profissional_id, barbearia=barbearia)
    
    if request.method == 'POST':
        form = ProfissionalForm(request.POST, instance=profissional)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profissional atualizado com sucesso!')
            return redirect('barbearias:admin_profissionais_lista', slug=slug)
    else:
        form = ProfissionalForm(instance=profissional)
    
    # Calcular estatísticas do profissional
    agendamentos_pendentes = profissional.agendamento_set.filter(status='agendado').count()
    agendamentos_concluidos = profissional.agendamento_set.filter(status='concluido').count()
    
    context = {
        'barbearia': barbearia,
        'profissional': profissional,
        'form': form,
        'titulo': 'Editar Profissional',
        'botao': 'Salvar Alterações',
        'agendamentos_pendentes': agendamentos_pendentes,
        'agendamentos_concluidos': agendamentos_concluidos,
    }
    return render(request, 'barbearias/admin/profissional_form.html', context)

@barbeiro_required
def admin_profissional_deletar(request, slug, profissional_id):
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    profissional = get_object_or_404(Profissional, id=profissional_id, barbearia=barbearia)

    # Se o profissional tiver agendamentos, não permitir a exclusão
    if profissional.agendamento_set.exists():
        messages.error(request, 'Não é possível deletar um profissional que já possui agendamentos.')
        return redirect('barbearias:admin_profissionais_lista', slug=slug)

    if request.method == 'POST':
        profissional.delete()
        messages.success(request, 'Profissional deletado com sucesso!')
        return redirect('barbearias:admin_profissionais_lista', slug=slug)

    context = {
        'barbearia': barbearia,
        'profissional': profissional,
    }
    return render(request, 'barbearias/admin/profissional_deletar.html', context)

def cancelar_agendamento_cliente(request, slug, agendamento_id):
    """Cancelar agendamento pelo cliente"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, barbearia=barbearia)
    
    if request.method == 'POST':
        telefone = request.POST.get('telefone', '').strip()
        
        # Verificar se o telefone corresponde ao agendamento
        if not telefone or agendamento.telefone_cliente != telefone:
            messages.error(request, 'Telefone não corresponde ao agendamento.')
            return redirect('barbearias:consultar_agendamentos_local', slug=slug)
        
        # Verificar se o agendamento pode ser cancelado
        if agendamento.status not in ['agendado', 'confirmado']:
            messages.error(request, 'Este agendamento não pode ser cancelado.')
            return redirect('barbearias:consultar_agendamentos_local', slug=slug)
        
        # Verificar se não está muito próximo da data/hora do agendamento
        from datetime import datetime, timedelta
        agora = timezone.now()
        limite_cancelamento = agendamento.data_hora - timedelta(hours=2)  # 2 horas antes
        
        if agora > limite_cancelamento:
            messages.error(request, 'Não é possível cancelar agendamentos com menos de 2 horas de antecedência.')
            return redirect('barbearias:consultar_agendamentos_local', slug=slug)
        
        # Cancelar o agendamento
        agendamento.status = 'cancelado'
        agendamento.save()
        
        messages.success(request, f'Agendamento de {agendamento.data_hora.strftime("%d/%m/%Y às %H:%M")} foi cancelado com sucesso.')
        
        # Redirecionar de volta para consulta mantendo o telefone
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        url = reverse('barbearias:consultar_agendamentos_local', kwargs={'slug': slug})
        return HttpResponseRedirect(f"{url}?telefone={telefone}")
    
    return redirect('barbearias:consultar_agendamentos_local', slug=slug)

@require_http_methods(["GET"])
def api_horarios_disponiveis(request, slug):
    """API para consultar horários disponíveis de um profissional"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    profissional_id = request.GET.get('profissional_id')
    data_str = request.GET.get('data')
    servico_id = request.GET.get('servico_id')
    
    if not all([profissional_id, data_str, servico_id]):
        return JsonResponse({
            'erro': 'Parâmetros obrigatórios: profissional_id, data, servico_id'
        }, status=400)
    
    try:
        profissional = get_object_or_404(Profissional, id=profissional_id, barbearia=barbearia, ativo=True)
        servico = get_object_or_404(Servico, id=servico_id, barbearia=barbearia, ativo=True)
        
        # Converter string de data para objeto date
        from datetime import datetime
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Verificar se a barbearia está fechada no dia da semana
        dia_semana = data.weekday()
        horario_funcionamento = HorarioFuncionamento.objects.filter(barbearia=barbearia, dia_semana=dia_semana).first()
        
        if horario_funcionamento and horario_funcionamento.fechado:
            return JsonResponse({
                'horarios': [],
                'profissional': profissional.nome,
                'servico': servico.nome,
                'duracao': servico.duracao_minutos,
                'data': data_str,
                'mensagem': 'O estabelecimento está fechado neste dia.'
            })

        # Obter horários disponíveis
        horarios = Agendamento.obter_horarios_disponiveis(
            profissional=profissional,
            data=data,
            duracao_minutos=servico.duracao_minutos
        )
        
        return JsonResponse({
            'horarios': horarios,
            'profissional': profissional.nome,
            'servico': servico.nome,
            'duracao': servico.duracao_minutos,
            'data': data_str
        })
        
    except ValueError as e:
        return JsonResponse({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

def api_dias_fechados(request, slug):
    """API para obter dias da semana em que a barbearia está fechada"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    # Buscar horários de funcionamento onde fechado=True
    horarios_fechados = HorarioFuncionamento.objects.filter(
        barbearia=barbearia, 
        fechado=True
    ).values_list('dia_semana', flat=True)
    
    return JsonResponse({
        'dias_fechados': list(horarios_fechados)
    })

@barbeiro_required
def admin_agenda_profissional(request, slug, profissional_id):
    """Visualizar agenda de um profissional específico"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    profissional = get_object_or_404(Profissional, id=profissional_id, barbearia=barbearia)
    
    # Data selecionada (default hoje)
    data_str = request.GET.get('data', timezone.now().date().strftime('%Y-%m-%d'))
    try:
        from datetime import datetime
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        data_selecionada = timezone.now().date()
    
    # Buscar agendamentos do profissional para a data
    agendamentos = Agendamento.objects.filter(
        profissional=profissional,
        data_hora__date=data_selecionada,
        status__in=['agendado', 'confirmado']
    ).order_by('data_hora')
    
    # Gerar horários do dia (8h às 18h)
    from datetime import datetime, time, timedelta
    horarios_dia = []
    hora_inicio = time(8, 0)  # 8:00
    hora_fim = time(18, 0)    # 18:00
    
    hora_atual = datetime.combine(data_selecionada, hora_inicio)
    hora_limite = datetime.combine(data_selecionada, hora_fim)
    
    while hora_atual <= hora_limite:
        # Verificar se há agendamento neste horário
        agendamento_neste_horario = None
        for agendamento in agendamentos:
            inicio_agendamento = agendamento.data_hora
            fim_agendamento = inicio_agendamento + timedelta(minutes=agendamento.servico.duracao_minutos)
            
            if inicio_agendamento <= hora_atual < fim_agendamento:
                agendamento_neste_horario = agendamento
                break
        
        horarios_dia.append({
            'hora': hora_atual.strftime('%H:%M'),
            'datetime': hora_atual,
            'agendamento': agendamento_neste_horario,
            'disponivel': agendamento_neste_horario is None
        })
        
        hora_atual += timedelta(minutes=30)  # Intervalos de 30 minutos
    
    context = {
        'barbearia': barbearia,
        'profissional': profissional,
        'data_selecionada': data_selecionada,
        'horarios_dia': horarios_dia,
        'agendamentos': agendamentos,
    }
    return render(request, 'barbearias/admin/agenda_profissional.html', context)

@barbeiro_required
def admin_horarios_funcionamento(request, slug):
    """Gerenciar horários de funcionamento da barbearia"""
    barbearia = get_object_or_404(Barbearia, slug=slug, usuario=request.user, ativa=True)

    # Obter ou criar instâncias de HorarioFuncionamento para cada dia da semana
    horarios_existentes = {h.dia_semana: h for h in HorarioFuncionamento.objects.filter(barbearia=barbearia)}
    
    # Criar uma lista de formulários, um para cada dia da semana
    forms = []
    for dia_num, dia_nome in HorarioFuncionamento.DIAS_DA_SEMANA:
        instance = horarios_existentes.get(dia_num)
        initial_data = {'dia_semana': dia_num} # Garante que o dia da semana esteja no formulário
        
        if request.method == 'POST':
            # Para cada dia, precisamos de um prefixo único para o formset
            form = HorarioFuncionamentoForm(request.POST, instance=instance, prefix=f'dia_{dia_num}')
        else:
            form = HorarioFuncionamentoForm(instance=instance, initial=initial_data, prefix=f'dia_{dia_num}')
        
        forms.append({'dia_nome': dia_nome, 'form': form})

    if request.method == 'POST':
        all_forms_valid = True
        forms_to_process = []

        # Criar uma cópia mutável de request.POST
        post_data = request.POST.copy()

        for dia_num, dia_nome in HorarioFuncionamento.DIAS_DA_SEMANA:
            instance = horarios_existentes.get(dia_num)
            
            # Garantir que dia_semana esteja em post_data para este formulário
            post_data[f'dia_{dia_num}-dia_semana'] = str(dia_num) # Converte para string para o POST data

            form = HorarioFuncionamentoForm(post_data, instance=instance, prefix=f'dia_{dia_num}')
            forms_to_process.append(form)

        for form in forms_to_process:
            if form.is_valid():
                fechado = form.cleaned_data['fechado']
                abertura = form.cleaned_data['abertura']
                fechamento = form.cleaned_data['fechamento']

                if fechado:
                    # Se fechado, garantir que abertura e fechamento sejam None
                    form.cleaned_data['abertura'] = None
                    form.cleaned_data['fechamento'] = None
                elif not abertura or not fechamento:
                    # Se não está fechado, mas faltam horários, é um erro
                    form.add_error('abertura', "Obrigatório se não estiver fechado.")
                    form.add_error('fechamento', "Obrigatório se não estiver fechado.")
                    all_forms_valid = False
                elif abertura and fechamento and abertura >= fechamento:
                    form.add_error('fechamento', "Deve ser depois do horário de abertura.")
                    all_forms_valid = False
            else:
                all_forms_valid = False
        
        if all_forms_valid:
            for form in forms_to_process:
                # Salvar apenas se o formulário for válido após todas as validações
                horario = form.save(commit=False)
                horario.barbearia = barbearia
                horario.dia_semana = form.cleaned_data['dia_semana']
                horario.abertura = form.cleaned_data['abertura']
                horario.fechamento = form.cleaned_data['fechamento']
                horario.save()
            messages.success(request, 'Horários de funcionamento atualizados com sucesso!')
            return redirect('barbearias:admin_horarios_funcionamento', slug=slug)
        else:
            messages.error(request, 'Por favor, corrija os erros nos horários.')

        # Re-renderizar formulários com erros
        forms = []
        for dia_num, dia_nome in HorarioFuncionamento.DIAS_DA_SEMANA:
            instance = horarios_existentes.get(dia_num)
            # Passar post_data para o formulário para que ele mantenha os valores submetidos
            form = HorarioFuncionamentoForm(post_data, instance=instance, prefix=f'dia_{dia_num}')
            forms.append({'dia_nome': dia_nome, 'form': form})

    context = {
        'barbearia': barbearia,
        'forms': forms,
    }
    return render(request, 'barbearias/admin/horarios_funcionamento.html', context)

@barbeiro_required
def admin_configuracoes(request, slug):
    """Configurações da barbearia"""
    barbearia = get_object_or_404(Barbearia, slug=slug, usuario=request.user, ativa=True)
    
    if request.method == 'POST':
        form = BarbeariaConfigForm(request.POST, instance=barbearia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações atualizadas com sucesso!')
            return redirect('barbearias:admin_configuracoes', slug=slug)
    else:
        form = BarbeariaConfigForm(instance=barbearia)
    
    context = {
        'barbearia': barbearia,
        'form': form,
    }
    return render(request, 'barbearias/admin/configuracoes.html', context)