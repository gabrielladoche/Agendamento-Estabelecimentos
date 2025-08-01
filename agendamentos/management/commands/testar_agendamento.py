from django.core.management.base import BaseCommand
from barbearias.models import Barbearia, Servico, Profissional
from agendamentos.models import Agendamento
from agendamentos.utils import enviar_notificacao_novo_agendamento
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Testa criação de agendamento e envio de notificação'

    def handle(self, *args, **options):
        try:
            # Buscar dados necessários
            barbearia = Barbearia.objects.get(slug='barbearia-teste')
            servico = Servico.objects.filter(barbearia=barbearia, ativo=True).first()
            profissional = Profissional.objects.filter(barbearia=barbearia, ativo=True).first()

            self.stdout.write(f'🏪 Barbearia: {barbearia.nome}')
            self.stdout.write(f'📧 Email: {barbearia.email_notificacoes}')
            self.stdout.write(f'💼 Serviço: {servico.nome}')
            self.stdout.write(f'👨‍💼 Profissional: {profissional.nome}')
            
            # Encontrar horário livre
            data_teste = timezone.now() + timedelta(days=2)
            data_teste = data_teste.replace(hour=10, minute=0, second=0, microsecond=0)
            
            self.stdout.write(f'📅 Data teste: {data_teste.strftime("%d/%m/%Y %H:%M")}')

            # Verificar se horário está livre
            conflito = Agendamento.objects.filter(
                profissional=profissional,
                data_hora=data_teste,
                status__in=['agendado', 'confirmado']
            ).exists()
            
            if conflito:
                self.stdout.write(self.style.WARNING('⚠️ Horário ocupado, usando horário alternativo'))
                data_teste = data_teste.replace(hour=16, minute=30)

            # Criar agendamento de teste
            agendamento = Agendamento(
                nome_cliente='Teste Sistema',
                telefone_cliente='11999887766',
                email_cliente='teste@sistema.com',
                servico=servico,
                profissional=profissional,
                barbearia=barbearia,
                data_hora=data_teste,
                observacoes='Teste automático de notificação'
            )
            
            # Salvar (vai chamar full_clean automaticamente)
            agendamento.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Agendamento #{agendamento.id} criado com sucesso!'))

            # Tentar enviar notificação
            self.stdout.write('📧 Enviando notificação...')
            
            resultado = enviar_notificacao_novo_agendamento(agendamento)
            
            if resultado:
                self.stdout.write(self.style.SUCCESS('✅ Notificação enviada com sucesso!'))
            else:
                self.stdout.write(self.style.ERROR('❌ Falha ao enviar notificação'))
                
            # Limpar dados de teste
            agendamento.delete()
            self.stdout.write('🧹 Agendamento de teste removido')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'🚨 Erro: {str(e)}'))