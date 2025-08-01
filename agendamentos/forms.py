from django import forms
from .models import Agendamento
from barbearias.models import Servico, Profissional
from django.utils import timezone
from datetime import datetime, timedelta

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['nome_cliente', 'telefone_cliente', 'email_cliente', 'servico', 'profissional', 'data_hora', 'observacoes']
        widgets = {
            'nome_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome completo'}),
            'telefone_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
            'email_cliente': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com (para lembretes)', 'required': True}),
            'data_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações adicionais (opcional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.barbearia = kwargs.pop('barbearia', None)
        super().__init__(*args, **kwargs)
        
        if self.barbearia:
            self.fields['servico'].queryset = Servico.objects.filter(barbearia=self.barbearia, ativo=True)
            self.fields['profissional'].queryset = Profissional.objects.filter(barbearia=self.barbearia, ativo=True)
        
        self.fields['servico'].widget.attrs.update({'class': 'form-control'})
        self.fields['profissional'].widget.attrs.update({'class': 'form-control'})
        
        # Define horário mínimo como agora + 1 hora
        min_datetime = (timezone.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
        self.fields['data_hora'].widget.attrs.update({'min': min_datetime})
    
    def clean_data_hora(self):
        data_hora = self.cleaned_data.get('data_hora')
        if not self.barbearia:
            raise forms.ValidationError("Barbearia não encontrada.")

        if data_hora:
            if data_hora < timezone.now():
                raise forms.ValidationError("Não é possível agendar para datas passadas.")

            dia_semana = data_hora.weekday()
            horario_funcionamento = self.barbearia.horarios_funcionamento.filter(dia_semana=dia_semana).first()

            if horario_funcionamento and horario_funcionamento.fechado:
                raise forms.ValidationError(f"A barbearia está fechada na {horario_funcionamento.get_dia_semana_display()}.")

        return data_hora
    
    def clean_telefone_cliente(self):
        telefone = self.cleaned_data.get('telefone_cliente')
        # Remove caracteres não numéricos
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        if len(telefone_limpo) < 10:
            raise forms.ValidationError("Número de telefone inválido.")
        return telefone
