from django.core.management.base import BaseCommand
from agendamentos.models import Agendamento
from agendamentos.utils import enviar_notificacao_novo_agendamento


class Command(BaseCommand):
    help = 'Testa o envio de notificação de novo agendamento'

    def add_arguments(self, parser):
        parser.add_argument('agendamento_id', type=int, help='ID do agendamento para testar')

    def handle(self, *args, **options):
        agendamento_id = options['agendamento_id']
        
        try:
            agendamento = Agendamento.objects.get(id=agendamento_id)
            
            self.stdout.write(f'📧 Testando notificação para agendamento #{agendamento.id}')
            self.stdout.write(f'Cliente: {agendamento.nome_cliente}')
            self.stdout.write(f'Email da barbearia: {agendamento.barbearia.email_notificacoes or "NÃO CONFIGURADO"}')
            
            if not agendamento.barbearia.email_notificacoes:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  A barbearia não tem email de notificações configurado!'
                    )
                )
                return
            
            # Enviar notificação
            resultado = enviar_notificacao_novo_agendamento(agendamento)
            
            if resultado:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Notificação enviada com sucesso para {agendamento.barbearia.email_notificacoes}!'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        '❌ Erro ao enviar notificação!'
                    )
                )
                
        except Agendamento.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Agendamento #{agendamento_id} não encontrado!'
                )
            )