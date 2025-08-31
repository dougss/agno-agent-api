#!/bin/bash

# Script para aplicar migrations do banco de dados
# Uso: ./scripts/apply_migrations.sh

set -e

echo "🗄️  Aplicando migrations do banco de dados..."

# Configurações do banco (ajuste conforme necessário)
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5532"}
DB_NAME=${DB_NAME:-"ai"}
DB_USER=${DB_USER:-"ai"}
DB_PASSWORD=${DB_PASSWORD:-"ai"}

# Verificar se Docker está disponível
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker."
    exit 1
fi

# Verificar se o container PostgreSQL está rodando
if ! docker ps | grep -q "pgvector"; then
    echo "❌ Container PostgreSQL não está rodando. Execute 'docker compose up -d' primeiro."
    exit 1
fi

# Função para aplicar migration usando Docker
apply_migration() {
    local migration_file=$1
    local migration_name=$(basename "$migration_file" .sql)
    
    echo "📝 Aplicando migration: $migration_name"
    
    # Usar docker exec para executar psql dentro do container
    docker exec -i $(docker ps -q --filter "name=pgvector") psql -U $DB_USER -d $DB_NAME < "$migration_file"
    
    if [ $? -eq 0 ]; then
        echo "✅ Migration $migration_name aplicada com sucesso"
    else
        echo "❌ Erro ao aplicar migration $migration_name"
        exit 1
    fi
}

# Aplicar migrations em ordem
echo "🔧 Aplicando schema do sistema multi-agentes..."

# Migration 001: Dynamic Agents System
if [ -f "migrations/001_dynamic_agents.sql" ]; then
    apply_migration "migrations/001_dynamic_agents.sql"
else
    echo "❌ Arquivo de migration não encontrado: migrations/001_dynamic_agents.sql"
    exit 1
fi

echo ""
echo "🎉 Todas as migrations foram aplicadas com sucesso!"
echo ""
echo "📊 Tabelas criadas:"
echo "   - dynamic_agents"
echo "   - available_tools" 
echo "   - dynamic_agent_sessions"
echo "   - dynamic_agent_runs"
echo "   - agent_specifications"
echo "   - dynamic_knowledge_bases"
echo ""
echo "🚀 Sistema multi-agentes pronto para uso!"
