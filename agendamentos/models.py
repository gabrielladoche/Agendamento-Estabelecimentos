from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from barbearias.models import Barbearia, Servico, Profissional
from datetime import datetime, timedelta

class Agendamento(models.Model):
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
        ('concluido', 'Concluído'),
    ]
    
    nome_cliente = models.CharField(max_length=200)
    telefone_cliente = models.CharField(max_length=20)
    email_cliente = models.EmailField(blank=False, null=True, help_text="Email para receber lembretes do agendamento")
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE)
    barbearia = models.ForeignKey(Barbearia, on_delete=models.CASCADE)
    data_hora = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendado')
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    notificacao_enviada = models.BooleanField(default=False)
    
    def clean(self):
        # Validação para evitar agendamentos no passado
        if self.data_hora and self.data_hora < timezone.now():
            raise ValidationError("Não é possível agendar para datas passadas.")
        
        # Validação para evitar conflitos de horário
        if self.data_hora and self.profissional and self.servico:
            inicio = self.data_hora
            fim = inicio + timedelta(minutes=self.servico.duracao_minutos)
            
            # Busca agendamentos existentes para o mesmo profissional
            agendamentos_conflitantes = Agendamento.objects.filter(
                profissional=self.profissional,
                status__in=['agendado', 'confirmado']
            ).exclude(pk=self.pk)
            
            for agendamento in agendamentos_conflitantes:
                agendamento_inicio = agendamento.data_hora
                agendamento_fim = agendamento_inicio + timedelta(minutes=agendamento.servico.duracao_minutos)
                
                # Verifica se há sobreposição de horários
                if (inicio < agendamento_fim and fim > agendamento_inicio):
                    raise ValidationError(f"Horário conflitante com agendamento existente de {agendamento.nome_cliente} às {agendamento_inicio.strftime('%H:%M')}")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome_cliente} - {self.servico.nome} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @staticmethod
    def verificar_disponibilidade(profissional, data_hora, duracao_minutos, agendamento_id=None):
        """Verifica se um horário está disponível para o profissional"""
        inicio = data_hora
        fim = inicio + timedelta(minutes=duracao_minutos)
        
        # Busca agendamentos conflitantes
        agendamentos_conflitantes = Agendamento.objects.filter(
            profissional=profissional,
            status__in=['agendado', 'confirmado']
        )
        
        if agendamento_id:
            agendamentos_conflitantes = agendamentos_conflitantes.exclude(pk=agendamento_id)
        
        for agendamento in agendamentos_conflitantes:
            agendamento_inicio = agendamento.data_hora
            agendamento_fim = agendamento_inicio + timedelta(minutes=agendamento.servico.duracao_minutos)
            
            # Verifica se há sobreposição
            if (inicio < agendamento_fim and fim > agendamento_inicio):
                return False, f"Conflito com agendamento de {agendamento.nome_cliente} às {agendamento_inicio.strftime('%H:%M')}"
        
        return True, "Horário disponível"
    
    @staticmethod
    def obter_horarios_disponiveis(profissional, data, duracao_minutos, horario_inicio='08:00', horario_fim='18:00', intervalo_minutos=30):
        """Obtém lista de horários disponíveis para um profissional em uma data específica"""
        from datetime import datetime, time
        
        horarios_disponiveis = []
        
        # Converter strings de horário para objetos time
        inicio = datetime.strptime(horario_inicio, '%H:%M').time()
        fim = datetime.strptime(horario_fim, '%H:%M').time()
        
        # Gerar horários possíveis com timezone
        hora_atual = timezone.make_aware(datetime.combine(data, inicio))
        hora_fim = timezone.make_aware(datetime.combine(data, fim))
        
        while hora_atual <= hora_fim - timedelta(minutes=duracao_minutos):
            # Verifica se não é no passado
            if hora_atual > timezone.now():
                disponivel, _ = Agendamento.verificar_disponibilidade(
                    profissional, hora_atual, duracao_minutos
                )
                if disponivel:
                    horarios_disponiveis.append({
                        'hora': hora_atual.strftime('%H:%M'),
                        'datetime': hora_atual.isoformat()
                    })
            
            hora_atual += timedelta(minutes=intervalo_minutos)
        
        return horarios_disponiveis
    
    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['-data_hora']
