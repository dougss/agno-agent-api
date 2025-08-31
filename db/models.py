from sqlalchemy import Column, String, Text, Boolean, Integer, Float, DateTime, JSON, ForeignKey, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class DynamicAgent(Base):
    __tablename__ = "dynamic_agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    role = Column(String(255))
    specialization = Column(String(255))
    
    # Configurações
    model_config = Column(JSON, nullable=False, default=dict)
    tools_config = Column(JSON, nullable=False, default=list)
    instructions = Column(JSON, nullable=False, default=dict)
    system_message = Column(Text)
    
    # Features
    reasoning_enabled = Column(Boolean, default=False)
    memory_enabled = Column(Boolean, default=False)
    knowledge_enabled = Column(Boolean, default=False)
    
    # Metadados
    status = Column(String(50), default="active")
    created_by = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Métricas
    total_sessions = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0)
    success_rate = Column(Float, default=0)
    last_used_at = Column(DateTime)


class AvailableTool(Base):
    __tablename__ = "available_tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    class_path = Column(String(500), nullable=False)
    category = Column(String(100))
    
    # Schema
    config_schema = Column(JSON, default=dict)
    required_env_vars = Column(JSON, default=list)
    
    # Custos e limites
    cost_per_call = Column(Float, default=0)
    rate_limit_per_minute = Column(Integer, default=60)
    
    # Metadados
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class DynamicAgentSession(Base):
    __tablename__ = "dynamic_agent_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_agents.id", ondelete="CASCADE"))
    user_id = Column(String(255))
    session_id = Column(String(255))
    
    # Estado
    session_state = Column(JSON, default=dict)
    total_messages = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime)
    
    # Relacionamentos
    agent = relationship("DynamicAgent", backref="sessions")
    runs = relationship("DynamicAgentRun", backref="session", cascade="all, delete-orphan")


class DynamicAgentRun(Base):
    __tablename__ = "dynamic_agent_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_agent_sessions.id", ondelete="CASCADE"))
    
    # Conteúdo
    input_message = Column(Text, nullable=False)
    response_text = Column(Text)
    tool_calls = Column(JSON, default=list)
    reasoning_steps = Column(JSON, default=list)
    
    # Métricas
    duration_ms = Column(Integer)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0)
    
    # Status
    status = Column(String(50), default="completed")
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)


class AgentSpecification(Base):
    __tablename__ = "agent_specifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Especificação
    specification = Column(JSON, nullable=False)
    
    # Metadados
    status = Column(String(50), default="pending")
    validation_errors = Column(JSON, default=list)
    created_agent_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_agents.id"))
    
    # Auditoria
    created_by = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    created_agent = relationship("DynamicAgent", backref="specifications")


class DynamicKnowledgeBase(Base):
    __tablename__ = "dynamic_knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_agents.id", ondelete="CASCADE"))
    
    # Configuração
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    sources = Column(JSON, nullable=False, default=list)
    
    # Vector DB config
    vector_config = Column(JSON, default=dict)
    
    # Estado
    status = Column(String(50), default="created")
    last_updated = Column(DateTime)
    document_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    agent = relationship("DynamicAgent", backref="knowledge_bases")
