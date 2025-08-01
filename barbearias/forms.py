from django import forms
from django.contrib.auth import authenticate
from .models import Servico, Profissional, Barbearia

class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['nome', 'preco', 'duracao_minutos', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'Nome do serviço'
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'duracao_minutos': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'Duração em minutos',
                'min': '1'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            })
        }
        labels = {
            'nome': 'Nome do Serviço',
            'preco': 'Preço (R$)',
            'duracao_minutos': 'Duração (minutos)',
            'ativo': 'Serviço Ativo'
        }

class ProfissionalForm(forms.ModelForm):
    class Meta:
        model = Profissional
        fields = ['nome', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'Nome do profissional'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            })
        }
        labels = {
            'nome': 'Nome do Profissional',
            'ativo': 'Profissional Ativo'
        }

class LoginBarbeiroForm(forms.Form):
    usuario = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
            'placeholder': 'Nome de usuário'
        }),
        label='Usuário'
    )
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
            'placeholder': 'Sua senha'
        }),
        label='Senha'
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.slug = kwargs.pop('slug', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        usuario = cleaned_data.get('usuario')
        senha = cleaned_data.get('senha')
        
        if usuario and senha:
            # Verificar se o usuário existe e tem uma barbearia com este slug
            user = authenticate(self.request, username=usuario, password=senha) # Passar request para authenticate
            if user is None:
                raise forms.ValidationError('Usuário ou senha incorretos.')
            
            # Verificar se o usuário tem uma barbearia com este slug
            try:
                barbearia = Barbearia.objects.get(slug=self.slug, usuario=user, ativa=True)
                cleaned_data['user'] = user
                cleaned_data['barbearia'] = barbearia
            except Barbearia.DoesNotExist:
                raise forms.ValidationError('Você não tem permissão para acessar esta barbearia.')
        
        return cleaned_data

from .models import HorarioFuncionamento

class HorarioFuncionamentoForm(forms.ModelForm):
    class Meta:
        model = HorarioFuncionamento
        fields = ['dia_semana', 'abertura', 'fechamento', 'fechado']
        widgets = {
            'dia_semana': forms.HiddenInput(),
            'abertura': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'type': 'time'
            }),
            'fechamento': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'type': 'time'
            }),
            'fechado': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            })
        }
        labels = {
            'dia_semana': 'Dia da Semana',
            'abertura': 'Horário de Abertura',
            'fechamento': 'Horário de Fechamento',
            'fechado': 'Fechado o dia todo'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dia_semana'].required = False
        self.fields['abertura'].required = False
        self.fields['fechamento'].required = False


class BarbeariaConfigForm(forms.ModelForm):
    class Meta:
        model = Barbearia
        fields = ['nome', 'endereco', 'telefone', 'email_notificacoes']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'Nome do estabelecimento'
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'Endereço completo',
                'rows': 3
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': '(11) 99999-9999'
            }),
            'email_notificacoes': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'email@exemplo.com (opcional)'
            })
        }
        labels = {
            'nome': 'Nome do Estabelecimento',
            'endereco': 'Endereço',
            'telefone': 'Telefone',
            'email_notificacoes': 'Email para Notificações'
        }
        help_texts = {
            'email_notificacoes': 'Email onde você receberá notificações de novos agendamentos'
        }
