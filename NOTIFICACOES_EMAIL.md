# 📧 Sistema de Notificações por Email

Este sistema envia notificações automáticas por email para duas situações:
1. **Lembretes para clientes** 24 horas antes de seus agendamentos
2. **Notificações para estabelecimentos** quando um novo agendamento é realizado

## ✨ Funcionalidades

### 👤 Para Clientes:
- 📅 Lembrete automático 24h antes do agendamento
- 🎨 Email em HTML responsivo com design profissional
- 📱 Compatível com todos os clientes de email
- 🔒 Controle para evitar envio duplicado
- 📊 Relatório detalhado de envios

### 🏪 Para Estabelecimentos:
- 🔔 Notificação imediata quando cliente agendar
- 📋 Dados completos do cliente e agendamento
- ⚡ Alertas especiais para agendamentos urgentes (hoje/amanhã)
- 👥 Informações de contato do cliente
- 💰 Detalhes do serviço e valor

## 🚀 Como Configurar

### 1. Configuração de Email

Edite o arquivo `barbearia_system/settings.py`:

```python
# Para produção com Gmail:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'menulybusiness@@gmail.com'
EMAIL_HOST_PASSWORD = 'tpnoprhrpqlozwtz'
DEFAULT_FROM_EMAIL = 'Sistema de Agendamento <noreply@agendamento.com>'
```

#### Como obter senha de app do Gmail:
1. Acesse sua conta Google
2. Vá em "Segurança" → "Verificação em duas etapas"
3. Em "Senhas de app", gere uma nova senha
4. Use essa senha no `EMAIL_HOST_PASSWORD`

### 2. Configuração do Email de Notificações do Estabelecimento

No painel administrativo:
1. Acesse **Configurações** no menu lateral
2. Configure o **Email para Notificações**
3. Salve as configurações

### 3. Automatização com Cron

Para enviar lembretes automaticamente todos os dias:

```bash
# Editar crontab
crontab -e

# Adicionar linha para executar todo dia às 9:00
0 9 * * * /home/gabriell/Documentos/barbearia/enviar_notificacoes_diarias.sh >> /var/log/notificacoes.log 2>&1
```

### 4. Teste Manual

Para testar os envios:

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Testar lembretes de agendamento (24h antes)
python manage.py enviar_notificacoes

# Testar notificação de novo agendamento
python manage.py testar_notificacao [ID_DO_AGENDAMENTO]
```

## 📋 Requisitos

### Para Lembretes (24h antes):
- Cliente deve ter email cadastrado no agendamento
- Agendamento deve estar com status 'agendado' ou 'confirmado'
- Data do agendamento deve estar entre 23.5h e 24.5h no futuro

### Para Notificações de Novo Agendamento:
- Estabelecimento deve ter email de notificações configurado
- Notificação é enviada imediatamente após a criação do agendamento

## 🎨 Template do Email

O email inclui:
- 👤 Nome do cliente
- 📅 Data e horário do agendamento
- 💼 Serviço contratado
- 👨‍💼 Profissional responsável
- 🏪 Nome do estabelecimento
- 💰 Preço do serviço
- ⏱️ Duração estimada
- 📝 Observações (se houver)

## 🔧 Comandos Úteis

```bash
# Testar configuração de email
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Teste', 'Mensagem teste', 'from@example.com', ['to@example.com'])

# Ver logs do cron
tail -f /var/log/notificacoes.log

# Executar script manualmente
./enviar_notificacoes_diarias.sh
```

## 🚨 Importante para Produção

1. **Nunca commite credenciais** - Use variáveis de ambiente:
   ```python
   import os
   EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
   EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
   ```

2. **Configure DNS reverso** para evitar spam

3. **Use domínio próprio** em produção

4. **Monitor logs** regularmente para identificar problemas

## 📊 Relatório de Envios

O comando gera um relatório mostrando:
- ✅ Quantos emails foram enviados
- ❌ Quantos falharam
- 📅 Janela de tempo considerada
- 📧 Lista detalhada por cliente

## 🐛 Solução de Problemas

### Email não enviado?
- Verifique credenciais Gmail
- Confirme que 2FA está ativo
- Use senha de app (não senha da conta)
- Verifique se email do cliente está correto

### Cron não executando?
- Teste o script manualmente primeiro
- Verifique permissões de execução
- Confirme caminhos absolutos no script
- Verifique logs em `/var/log/cron`