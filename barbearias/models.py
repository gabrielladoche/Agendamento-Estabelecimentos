from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Barbearia(models.Model):
    nome = models.CharField(max_length=200)
    endereco = models.TextField()
    telefone = models.CharField(max_length=20)
    email_notificacoes = models.EmailField(blank=True, null=True, help_text="Email para receber notificações de novos agendamentos")
    slug = models.SlugField(unique=True, max_length=200)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Estabelecimento"
        verbose_name_plural = "Estabelecimentos"

class Servico(models.Model):
    nome = models.CharField(max_length=200)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracao_minutos = models.PositiveIntegerField(help_text="Duração do serviço em minutos")
    barbearia = models.ForeignKey(Barbearia, on_delete=models.CASCADE, related_name='servicos')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - {self.barbearia.nome}"
    
    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

class Profissional(models.Model):
    nome = models.CharField(max_length=200)
    barbearia = models.ForeignKey(Barbearia, on_delete=models.CASCADE, related_name='profissionais')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - {self.barbearia.nome}"
    
    class Meta:
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"


class HorarioFuncionamento(models.Model):
    DIAS_DA_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    barbearia = models.ForeignKey(Barbearia, on_delete=models.CASCADE, related_name='horarios_funcionamento')
    dia_semana = models.IntegerField(choices=DIAS_DA_SEMANA, unique=False)
    abertura = models.TimeField(null=True, blank=True)
    fechamento = models.TimeField(null=True, blank=True)
    fechado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Horário de Funcionamento"
        verbose_name_plural = "Horários de Funcionamento"
        unique_together = ('barbearia', 'dia_semana')
        ordering = ['dia_semana']

    def __str__(self):
        dia = self.get_dia_semana_display()
        if self.fechado:
            return f"{dia} - Fechado"
        return f"{dia} - {self.abertura.strftime('%H:%M')} às {self.fechamento.strftime('%H:%M')}"
