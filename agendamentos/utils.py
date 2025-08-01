from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def enviar_notificacao_novo_agendamento(agendamento):
    """
    Envia notificação por email para o estabelecimento quando um novo agendamento é criado
    """
    # Verificar se a barbearia tem email configurado
    if not agendamento.barbearia.email_notificacoes:
        logger.info(f"Barbearia {agendamento.barbearia.nome} não tem email de notificações configurado")
        return False
    
    try:
        # Assunto do email
        assunto = f'🆕 Novo Agendamento - {agendamento.nome_cliente} ({agendamento.data_hora.strftime("%d/%m/%Y %H:%M")})'
        
        # Mensagem em texto simples
        mensagem_texto = f"""
NOVO AGENDAMENTO RECEBIDO!

Cliente: {agendamento.nome_cliente}
Telefone: {agendamento.telefone_cliente}
Email: {agendamento.email_cliente}

Data: {agendamento.data_hora.strftime('%d/%m/%Y')}
Horário: {agendamento.data_hora.strftime('%H:%M')}
Serviço: {agendamento.servico.nome}
Profissional: {agendamento.profissional.nome}
Valor: R$ {agendamento.servico.preco}
Duração: {agendamento.servico.duracao_minutos} minutos

{f"Observações: {agendamento.observacoes}" if agendamento.observacoes else ""}

ID do Agendamento: #{agendamento.id}
Status: {agendamento.get_status_display()}
Agendamento realizado em: {agendamento.criado_em.strftime('%d/%m/%Y %H:%M')}

---
{agendamento.barbearia.nome}
Sistema de Agendamento
"""
        
        # Calcular se é hoje ou amanhã para o template
        from datetime import date, timedelta
        hoje = date.today()
        amanha = hoje + timedelta(days=1)
        
        # Renderizar template HTML
        mensagem_html = render_to_string('emails/novo_agendamento.html', {
            'agendamento': agendamento,
            'hoje': hoje,
            'amanha': amanha
        })
        
        # Criar email com versão HTML e texto
        email = EmailMultiAlternatives(
            subject=assunto,
            body=mensagem_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[agendamento.barbearia.email_notificacoes]
        )
        email.attach_alternative(mensagem_html, "text/html")
        email.send()
        
        logger.info(f"Notificação de novo agendamento enviada para {agendamento.barbearia.email_notificacoes}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação de novo agendamento: {str(e)}")
        return False


def enviar_notificacao_cancelamento(agendamento, motivo=""):
    """
    Envia notificação por email para o estabelecimento quando um agendamento é cancelado
    """
    # Verificar se a barbearia tem email configurado
    if not agendamento.barbearia.email_notificacoes:
        return False
    
    try:
        # Assunto do email
        assunto = f'❌ Agendamento Cancelado - {agendamento.nome_cliente} ({agendamento.data_hora.strftime("%d/%m/%Y %H:%M")})'
        
        # Mensagem em texto simples
        mensagem_texto = f"""
AGENDAMENTO CANCELADO

Cliente: {agendamento.nome_cliente}
Telefone: {agendamento.telefone_cliente}

Data: {agendamento.data_hora.strftime('%d/%m/%Y')}
Horário: {agendamento.data_hora.strftime('%H:%M')}
Serviço: {agendamento.servico.nome}
Profissional: {agendamento.profissional.nome}

{f"Motivo: {motivo}" if motivo else ""}

ID do Agendamento: #{agendamento.id}

---
{agendamento.barbearia.nome}
Sistema de Agendamento
"""
        
        # Criar email simples para cancelamento
        email = EmailMultiAlternatives(
            subject=assunto,
            body=mensagem_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[agendamento.barbearia.email_notificacoes]
        )
        email.send()
        
        logger.info(f"Notificação de cancelamento enviada para {agendamento.barbearia.email_notificacoes}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação de cancelamento: {str(e)}")
        return False