from typing import Optional, List
from logging import getLogger
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
import json
import uuid

from core.dynamic_agent_factory import agent_factory
from db.session import get_db, SessionLocal
from db.models import DynamicAgent, DynamicAgentSession, DynamicAgentRun

logger = getLogger(__name__)

dynamic_agents_router = APIRouter(prefix="/dynamic-agents", tags=["Dynamic Agents"])


def validate_uuid(uuid_string: str) -> bool:
    """Valida se uma string é um UUID válido"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


class AgentChatRequest(BaseModel):
    """Request para chat com agente dinâmico"""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = True


class AgentUpdateRequest(BaseModel):
    """Request para atualização de agente"""
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None


@dynamic_agents_router.get("/")
async def list_dynamic_agents(
    specialization: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Lista agentes dinâmicos com filtros e paginação
    """
    try:
        db = SessionLocal()
        try:
            query = db.query(DynamicAgent)
            
            if specialization:
                query = query.filter(DynamicAgent.specialization == specialization)
            
            if status:
                query = query.filter(DynamicAgent.status == status)
            
            # Contar total
            total = query.count()
            
            # Aplicar paginação
            agents = query.order_by(DynamicAgent.created_at.desc()).offset(offset).limit(limit).all()
            
            # Converter para dict
            agents_data = []
            for agent in agents:
                agents_data.append({
                    "id": str(agent.id),
                    "name": agent.name,
                    "slug": agent.slug,
                    "description": agent.description,
                    "role": agent.role,
                    "specialization": agent.specialization,
                    "status": agent.status,
                    "created_at": agent.created_at.isoformat() if agent.created_at else None,
                    "metrics": {
                        "total_sessions": agent.total_sessions,
                        "avg_response_time_ms": agent.avg_response_time_ms,
                        "success_rate": agent.success_rate,
                        "last_used_at": agent.last_used_at.isoformat() if agent.last_used_at else None
                    }
                })
            
            return {
                "agents": agents_data,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Erro listando agentes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@dynamic_agents_router.get("/{agent_id}")
async def get_agent_details(agent_id: str):
    """
    Obtém detalhes completos de um agente
    """
    try:
        db = SessionLocal()
        try:
            agent = db.query(DynamicAgent).filter(DynamicAgent.id == agent_id).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agente não encontrado"
                )
            
            agent_data = {
                "id": str(agent.id),
                "name": agent.name,
                "slug": agent.slug,
                "description": agent.description,
                "role": agent.role,
                "specialization": agent.specialization,
                "model_config": agent.model_config,
                "tools_config": agent.tools_config,
                "instructions": agent.instructions,
                "system_message": agent.system_message,
                "reasoning_enabled": agent.reasoning_enabled,
                "memory_enabled": agent.memory_enabled,
                "knowledge_enabled": agent.knowledge_enabled,
                "status": agent.status,
                "created_by": agent.created_by,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                "total_sessions": agent.total_sessions,
                "avg_response_time_ms": agent.avg_response_time_ms,
                "success_rate": agent.success_rate,
                "last_used_at": agent.last_used_at.isoformat() if agent.last_used_at else None
            }
            
            return agent_data
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro obtendo detalhes do agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@dynamic_agents_router.post("/{agent_id}/chat")
async def chat_with_dynamic_agent(agent_id: str, request: AgentChatRequest):
    """
    Chat com agente dinâmico específico
    """
    try:
        # Gerar session_id se não fornecido
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Criar ou buscar sessão no banco
        db = SessionLocal()
        try:
            # Verificar se a sessão já existe
            existing_session = db.query(DynamicAgentSession).filter(
                DynamicAgentSession.agent_id == agent_id,
                DynamicAgentSession.session_id == session_id
            ).first()
            
            if not existing_session:
                # Criar nova sessão
                session = DynamicAgentSession(
                    agent_id=agent_id,
                    user_id=request.user_id,
                    session_id=session_id,
                    session_state={},
                    total_messages=0
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            
            # Atualizar contador de sessões do agente
            agent = db.query(DynamicAgent).filter(DynamicAgent.id == agent_id).first()
            if agent:
                agent.total_sessions = agent.total_sessions + 1 if agent.total_sessions else 1
                agent.last_used_at = datetime.now()
                db.commit()
                
        finally:
            db.close()
        
        # Carregar agente dinamicamente
        agent = await agent_factory.load_dynamic_agent(
            agent_id=agent_id,
            user_id=request.user_id,
            session_id=session_id
        )
        
        if request.stream:
            async def generate_response():
                # Primeiro, enviar evento de início com session_id
                yield f"data: {json.dumps({'event': 'RunStarted', 'session_id': session_id, 'created_at': int(datetime.now().timestamp())})}\n\n"
                
                # Depois, enviar a resposta do agente
                async for chunk in await agent.arun(request.message, stream=True):
                    if chunk.content:
                        yield f"data: {json.dumps({'event': 'RunResponseContent', 'content': chunk.content})}\n\n"
                
                # Finalizar com evento de conclusão
                yield f"data: {json.dumps({'event': 'RunCompleted'})}\n\n"
            
            return StreamingResponse(
                generate_response(),
                media_type="text/event-stream"
            )
        else:
            response = await agent.arun(request.message, stream=False)
            
            # Salvar a execução no banco
            db = SessionLocal()
            try:
                session = db.query(DynamicAgentSession).filter(
                    DynamicAgentSession.agent_id == agent_id,
                    DynamicAgentSession.session_id == session_id
                ).first()
                
                if session:
                    # Criar registro da execução
                    run = DynamicAgentRun(
                        session_id=session.id,
                        input_message=request.message,
                        response_text=response.content,
                        status="completed",
                        created_at=datetime.now(),
                        completed_at=datetime.now()
                    )
                    db.add(run)
                    
                    # Atualizar contadores da sessão
                    session.total_messages += 2  # input + response
                    session.last_message_at = datetime.now()
                    session.updated_at = datetime.now()
                    
                    db.commit()
                    
            finally:
                db.close()
            
            return {
                "content": response.content,
                "session_id": session_id,
                "created_at": int(datetime.now().timestamp())
            }
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro no chat com agente dinâmico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@dynamic_agents_router.put("/{agent_id}")
async def update_dynamic_agent(agent_id: str, request: AgentUpdateRequest):
    """
    Atualiza configurações de um agente dinâmico
    """
    try:
        db = SessionLocal()
        try:
            agent = db.query(DynamicAgent).filter(DynamicAgent.id == agent_id).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agente não encontrado"
                )
            
            # Atualizar campos fornecidos
            update_data = request.dict(exclude_unset=True)
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nenhum campo para atualizar"
                )
            
            for field, value in update_data.items():
                if hasattr(agent, field):
                    setattr(agent, field, value)
            
            agent.updated_at = datetime.now()
            db.commit()
            
            return {"message": "Agente atualizado com sucesso"}
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro atualizando agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@dynamic_agents_router.delete("/{agent_id}")
async def delete_dynamic_agent(agent_id: str):
    """
    Deleta um agente dinâmico (soft delete)
    """
    try:
        db = SessionLocal()
        try:
            agent = db.query(DynamicAgent).filter(
                DynamicAgent.id == agent_id,
                DynamicAgent.status != "deleted"
            ).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agente não encontrado ou já deletado"
                )
            
            agent.status = "deleted"
            agent.updated_at = datetime.now()
            db.commit()
            
            return {"message": "Agente deletado com sucesso"}
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro deletando agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@dynamic_agents_router.get("/{agent_id}/sessions")
async def get_dynamic_agent_sessions(agent_id: str):
    """
    Lista sessões de um agente dinâmico
    """
    try:
        # Validar UUID
        if not validate_uuid(agent_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID do agente inválido"
            )
        
        db = SessionLocal()
        try:
            # Verificar se o agente existe
            agent = db.query(DynamicAgent).filter(DynamicAgent.id == agent_id).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agente não encontrado"
                )
            
            # Buscar sessões do agente
            sessions = db.query(DynamicAgentSession).filter(
                DynamicAgentSession.agent_id == agent_id
            ).order_by(DynamicAgentSession.created_at.desc()).all()
            
            # Converter para formato compatível com o frontend
            sessions_data = []
            for session in sessions:
                # Buscar a primeira mensagem para usar como título
                first_run = db.query(DynamicAgentRun).filter(
                    DynamicAgentRun.session_id == session.id
                ).order_by(DynamicAgentRun.created_at.asc()).first()
                
                title = "Nova conversa"
                if first_run and first_run.input_message:
                    # Usar os primeiros 50 caracteres da primeira mensagem como título
                    title = first_run.input_message[:50]
                    if len(first_run.input_message) > 50:
                        title += "..."
                
                sessions_data.append({
                    "session_id": str(session.session_id),
                    "title": title,
                    "session_name": None,
                    "created_at": int(session.created_at.timestamp())
                })
            
            return sessions_data
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro listando sessões do agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@dynamic_agents_router.get("/{agent_id}/sessions/{session_id}")
async def get_dynamic_agent_session(agent_id: str, session_id: str):
    """
    Obtém detalhes de uma sessão específica de um agente dinâmico
    """
    try:
        # Validar UUIDs
        if not validate_uuid(agent_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID do agente inválido"
            )
        
        if not validate_uuid(session_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID da sessão inválido"
            )
        
        db = SessionLocal()
        try:
            # Verificar se o agente existe
            agent = db.query(DynamicAgent).filter(DynamicAgent.id == agent_id).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agente não encontrado"
                )
            
            # Buscar a sessão
            session = db.query(DynamicAgentSession).filter(
                DynamicAgentSession.agent_id == agent_id,
                DynamicAgentSession.session_id == session_id
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sessão não encontrada"
                )
            
            # Buscar todas as execuções da sessão
            runs = db.query(DynamicAgentRun).filter(
                DynamicAgentRun.session_id == session.id
            ).order_by(DynamicAgentRun.created_at.asc()).all()
            
            # Converter para formato compatível com o frontend
            messages = []
            for run in runs:
                # Adicionar mensagem do usuário
                messages.append({
                    "role": "user",
                    "content": run.input_message,
                    "timestamp": int(run.created_at.timestamp())
                })
                
                # Adicionar resposta do agente se existir
                if run.response_text:
                    messages.append({
                        "role": "assistant",
                        "content": run.response_text,
                        "timestamp": int(run.completed_at.timestamp()) if run.completed_at else int(run.created_at.timestamp())
                    })
            
            return {
                "session_id": str(session.session_id),
                "agent_id": agent_id,
                "messages": messages,
                "created_at": int(session.created_at.timestamp()),
                "updated_at": int(session.updated_at.timestamp())
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro obtendo sessão do agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@dynamic_agents_router.delete("/{agent_id}/sessions/{session_id}")
async def delete_dynamic_agent_session(agent_id: str, session_id: str):
    """
    Deleta uma sessão específica de um agente dinâmico
    """
    try:
        # Validar UUIDs
        if not validate_uuid(agent_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID do agente inválido"
            )
        
        if not validate_uuid(session_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID da sessão inválido"
            )
        
        db = SessionLocal()
        try:
            # Verificar se o agente existe
            agent = db.query(DynamicAgent).filter(DynamicAgent.id == agent_id).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agente não encontrado"
                )
            
            # Buscar a sessão
            session = db.query(DynamicAgentSession).filter(
                DynamicAgentSession.agent_id == agent_id,
                DynamicAgentSession.session_id == session_id
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sessão não encontrada"
                )
            
            # Deletar a sessão (cascade irá deletar as execuções também)
            db.delete(session)
            db.commit()
            
            return {"message": "Sessão deletada com sucesso"}
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro deletando sessão do agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@dynamic_agents_router.get("/{agent_id}/performance")
async def get_agent_performance(agent_id: str):
    """
    Obtém métricas detalhadas de performance do agente
    """
    try:
        db = SessionLocal()
        try:
            # Métricas básicas
            agent = db.query(DynamicAgent).filter(DynamicAgent.id == agent_id).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agente não encontrado"
                )
            
            overall_metrics = {
                "total_sessions": agent.total_sessions,
                "avg_response_time_ms": agent.avg_response_time_ms,
                "success_rate": agent.success_rate,
                "last_used_at": agent.last_used_at.isoformat() if agent.last_used_at else None,
                "created_at": agent.created_at.isoformat() if agent.created_at else None
            }
            
            # Métricas de execuções recentes (últimos 30 dias)
            from datetime import timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            recent_runs = db.query(DynamicAgentRun).join(DynamicAgentSession).filter(
                DynamicAgentSession.agent_id == agent_id,
                DynamicAgentRun.created_at >= thirty_days_ago
            ).all()
            
            # Agrupar por data
            performance_by_date = {}
            for run in recent_runs:
                date_key = run.created_at.date().isoformat()
                if date_key not in performance_by_date:
                    performance_by_date[date_key] = {
                        "total_runs": 0,
                        "total_duration": 0,
                        "total_tokens": 0,
                        "total_cost": 0
                    }
                
                performance_by_date[date_key]["total_runs"] += 1
                if run.duration_ms:
                    performance_by_date[date_key]["total_duration"] += run.duration_ms
                if run.tokens_used:
                    performance_by_date[date_key]["total_tokens"] += run.tokens_used
                if run.cost_usd:
                    performance_by_date[date_key]["total_cost"] += run.cost_usd
            
            # Calcular médias
            recent_performance = []
            for date, metrics in performance_by_date.items():
                recent_performance.append({
                    "date": date,
                    "total_runs": metrics["total_runs"],
                    "avg_duration": metrics["total_duration"] / metrics["total_runs"] if metrics["total_runs"] > 0 else 0,
                    "avg_tokens": metrics["total_tokens"] / metrics["total_runs"] if metrics["total_runs"] > 0 else 0,
                    "total_cost": metrics["total_cost"]
                })
            
            return {
                "agent_id": agent_id,
                "overall_metrics": overall_metrics,
                "recent_performance": recent_performance
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro obtendo performance do agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )
