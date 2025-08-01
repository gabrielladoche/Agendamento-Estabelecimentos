from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from agendamentos.models import Agendamento


class Command(BaseCommand):
    help = 'Envia notificações por email para agendamentos que acontecem em 24 horas'

    def handle(self, *args, **options):
        # Calcular data/hora de 24 horas à frente
        agora = timezone.now()
        amanha = agora + timedelta(hours=24)
        
        # Margem de 1 hora para capturar agendamentos próximos
        inicio_janela = amanha - timedelta(minutes=30)
        fim_janela = amanha + timedelta(minutes=30)
        
        # Buscar agendamentos que precisam de notificação
        agendamentos = Agendamento.objects.filter(
            data_hora__gte=inicio_janela,
            data_hora__lte=fim_janela,
            status__in=['agendado', 'confirmado'],
            email_cliente__isnull=False,
            email_cliente__gt='',
            notificacao_enviada=False
        )
        
        contador_enviados = 0
        contador_erros = 0
        
        for agendamento in agendamentos:
            try:
                # Enviar email de lembrete
                assunto = f'Lembrete: Seu agendamento em {agendamento.barbearia.nome}'
                
                # Mensagem em texto simples
                mensagem_texto = f"""
Olá {agendamento.nome_cliente},

Este é um lembrete do seu agendamento:

📅 Data: {agendamento.data_hora.strftime('%d/%m/%Y')}
⏰ Horário: {agendamento.data_hora.strftime('%H:%M')}
💼 Serviço: {agendamento.servico.nome}
👨‍💼 Profissional: {agendamento.profissional.nome}
🏪 Local: {agendamento.barbearia.nome}

Preço: R$ {agendamento.servico.preco}
Duração estimada: {agendamento.servico.duracao_minutos} minutos

{f"Observações: {agendamento.observacoes}" if agendamento.observacoes else ""}

Caso precise cancelar ou reagendar, entre em contato conosco com antecedência.

Obrigado por escolher nossos serviços!

---
Sistema de Agendamento
"""
                
                # Renderizar template HTML
                mensagem_html = render_to_string('emails/lembrete_agendamento.html', {
                    'agendamento': agendamento
                })
                
                # Criar email com versão HTML e texto
                email = EmailMultiAlternatives(
                    subject=assunto,
                    body=mensagem_texto,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[agendamento.email_cliente]
                )
                email.attach_alternative(mensagem_html, "text/html")
                email.send()
                
                # Marcar como notificação enviada
                agendamento.notificacao_enviada = True
                agendamento.save()
                
                contador_enviados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Notificação enviada para {agendamento.nome_cliente} ({agendamento.email_cliente})'
                    )
                )
                
            except Exception as e:
                contador_erros += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Erro ao enviar para {agendamento.nome_cliente} ({agendamento.email_cliente}): {str(e)}'
                    )
                )
        
        # Relatório final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'📊 RELATÓRIO DE NOTIFICAÇÕES')
        self.stdout.write('='*50)
        self.stdout.write(f'📧 Emails enviados com sucesso: {contador_enviados}')
        self.stdout.write(f'❌ Erros: {contador_erros}')
        self.stdout.write(f'📅 Janela de notificação: {inicio_janela.strftime("%d/%m/%Y %H:%M")} até {fim_janela.strftime("%d/%m/%Y %H:%M")}')
        
        if contador_enviados > 0:
            self.stdout.write(self.style.SUCCESS('\n✅ Comando executado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Nenhuma notificação para enviar no momento.'))