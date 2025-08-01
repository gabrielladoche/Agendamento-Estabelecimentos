#!/bin/bash

# Script para enviar notificações de agendamento diariamente
echo "🔔 Iniciando envio de notificações de agendamento..."
echo "Data/Hora: $(date '+%d/%m/%Y %H:%M:%S')"
echo "========================================"

# Navegar para o diretório do projeto
cd /home/gabriell/Documentos/barbearia

# Ativar o ambiente virtual
source venv/bin/activate

# Executar o comando de notificações
python manage.py enviar_notificacoes

echo "========================================"
echo "✅ Processo finalizado em $(date '+%d/%m/%Y %H:%M:%S')"
echo ""