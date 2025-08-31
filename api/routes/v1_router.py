from fastapi import APIRouter

from api.routes.agents import agents_router
from api.routes.health import health_router
from api.routes.playground import playground_router
from api.routes.agent_builder import agent_builder_router  # NOVO
from api.routes.dynamic_agents import dynamic_agents_router  # NOVO

v1_router = APIRouter(prefix="/v1")

# Routers existentes
v1_router.include_router(health_router)
v1_router.include_router(agents_router)
v1_router.include_router(playground_router)

# Novos routers para sistema multi-agentes
v1_router.include_router(agent_builder_router)
v1_router.include_router(dynamic_agents_router)
