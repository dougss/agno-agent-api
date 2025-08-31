-- Migration 001: Dynamic Agents System Schema
-- Data: 2024-12-19
-- Description: Schema completo para sistema multi-agentes com Meta-Agente Builder

-- Extensão do schema atual para suportar agentes dinâmicos

-- Tabela para agentes dinâmicos criados pelo meta-agente
CREATE TABLE IF NOT EXISTS dynamic_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    role VARCHAR(255),
    specialization VARCHAR(255),
    
    -- Configurações do modelo
    model_config JSONB NOT NULL DEFAULT '{}',
    
    -- Configurações de tools
    tools_config JSONB NOT NULL DEFAULT '[]',
    
    -- Instruções e prompts
    instructions JSONB NOT NULL DEFAULT '{}',
    system_message TEXT,
    
    -- Features habilitadas
    reasoning_enabled BOOLEAN DEFAULT false,
    memory_enabled BOOLEAN DEFAULT false,
    knowledge_enabled BOOLEAN DEFAULT false,
    
    -- Metadados
    status VARCHAR(50) DEFAULT 'active',
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Métricas de performance
    total_sessions INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT DEFAULT 0,
    success_rate FLOAT DEFAULT 0,
    last_used_at TIMESTAMP
);

-- Catálogo de tools disponíveis
CREATE TABLE IF NOT EXISTS available_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    class_path VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    
    -- Schema de configuração
    config_schema JSONB DEFAULT '{}',
    required_env_vars JSONB DEFAULT '[]',
    
    -- Custos e limites
    cost_per_call DECIMAL(10,6) DEFAULT 0,
    rate_limit_per_minute INTEGER DEFAULT 60,
    
    -- Metadados
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessões de agentes dinâmicos
CREATE TABLE IF NOT EXISTS dynamic_agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES dynamic_agents(id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Estado da sessão
    session_state JSONB DEFAULT '{}',
    total_messages INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP
);

-- Execuções individuais
CREATE TABLE IF NOT EXISTS dynamic_agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES dynamic_agent_sessions(id) ON DELETE CASCADE,
    
    -- Conteúdo da execução
    input_message TEXT NOT NULL,
    response_text TEXT,
    tool_calls JSONB DEFAULT '[]',
    reasoning_steps JSONB DEFAULT '[]',
    
    -- Métricas
    duration_ms INTEGER,
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'completed',
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Especificações geradas pelo meta-agente
CREATE TABLE IF NOT EXISTS agent_specifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Especificação completa em JSON
    specification JSONB NOT NULL,
    
    -- Metadados de criação
    status VARCHAR(50) DEFAULT 'pending', -- pending, validated, created, failed
    validation_errors JSONB DEFAULT '[]',
    created_agent_id UUID REFERENCES dynamic_agents(id),
    
    -- Auditoria
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge bases dinâmicas
CREATE TABLE IF NOT EXISTS dynamic_knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES dynamic_agents(id) ON DELETE CASCADE,
    
    -- Configuração
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- url, pdf, text, etc
    sources JSONB NOT NULL DEFAULT '[]',
    
    -- Vector DB config
    vector_config JSONB DEFAULT '{}',
    
    -- Estado
    status VARCHAR(50) DEFAULT 'created', -- created, loading, ready, error
    last_updated TIMESTAMP,
    document_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_dynamic_agents_status ON dynamic_agents(status);
CREATE INDEX IF NOT EXISTS idx_dynamic_agents_specialization ON dynamic_agents(specialization);
CREATE INDEX IF NOT EXISTS idx_dynamic_agent_sessions_agent_id ON dynamic_agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_dynamic_agent_runs_session_id ON dynamic_agent_runs(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_specifications_status ON agent_specifications(status);

-- Inserir tools padrão disponíveis
INSERT INTO available_tools (name, display_name, description, class_path, category, config_schema) VALUES
('DuckDuckGoTools', 'Web Search', 'Pesquisa na web usando DuckDuckGo', 'agno.tools.duckduckgo.DuckDuckGoTools', 'search', '{}'),
('YFinanceTools', 'Financial Data', 'Dados financeiros e de ações', 'agno.tools.yfinance.YFinanceTools', 'finance', '{"stock_price": "bool", "analyst_recommendations": "bool"}'),
('ReasoningTools', 'Reasoning', 'Ferramentas de raciocínio estruturado', 'agno.tools.reasoning.ReasoningTools', 'reasoning', '{"think": "bool", "analyze": "bool"}'),
('KnowledgeTools', 'Knowledge Base', 'Ferramentas para knowledge bases', 'agno.tools.knowledge.KnowledgeTools', 'knowledge', '{"think": "bool", "search": "bool", "analyze": "bool"}')
ON CONFLICT (name) DO NOTHING;

-- Comentários para documentação
COMMENT ON TABLE dynamic_agents IS 'Agentes criados dinamicamente pelo Meta-Agente Builder';
COMMENT ON TABLE available_tools IS 'Catálogo de tools disponíveis para criação de agentes';
COMMENT ON TABLE dynamic_agent_sessions IS 'Sessões de conversa com agentes dinâmicos';
COMMENT ON TABLE dynamic_agent_runs IS 'Execuções individuais de agentes dinâmicos';
COMMENT ON TABLE agent_specifications IS 'Especificações JSON geradas pelo meta-agente';
COMMENT ON TABLE dynamic_knowledge_bases IS 'Knowledge bases criadas automaticamente para agentes';
