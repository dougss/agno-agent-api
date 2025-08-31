# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- `./scripts/dev_setup.sh` - Create virtual environment and install dependencies using `uv`
- `source .venv/bin/activate` - Activate the virtual environment (required for development)
- `./scripts/generate_requirements.sh` - Generate requirements.txt from pyproject.toml
- `./scripts/generate_requirements.sh upgrade` - Upgrade all dependencies to latest compatible versions

### Code Quality
- `./scripts/validate.sh` - Run full validation (ruff lint + mypy type checking)
- `./scripts/format.sh` - Format code using ruff (includes import sorting)
- `ruff check .` - Lint code only
- `mypy . --config-file pyproject.toml` - Type check only

### Application
- `docker compose up -d` - Start the full application (FastAPI + PostgreSQL)
- `docker compose up -d --build` - Rebuild and start application
- `docker compose down` - Stop the application
- `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000` - Run API server in development mode

### Production
- `./scripts/build_image.sh` - Build and push production Docker image
- Update `scripts/build_image.sh` with your IMAGE_NAME and IMAGE_TAG before building

## Architecture Overview

This is an Agent API built on Agno framework that serves AI agents through FastAPI endpoints. The system supports both predefined and dynamically created agents.

### Core Components

**Agent Management**
- `agents/selector.py` - Central agent registry and factory for predefined agents
- `core/dynamic_agent_factory.py` - Factory for creating and loading dynamic agents with validation
- `agents/` - Predefined agent implementations (web, finance, agno_assist, meta_agent_builder)

**API Structure** 
- `api/main.py` - FastAPI app factory with CORS middleware
- `api/routes/v1_router.py` - Main API router including all endpoints
- `api/routes/agents.py` - Predefined agent endpoints
- `api/routes/dynamic_agents.py` - Dynamic agent CRUD endpoints
- `api/routes/agent_builder.py` - Agent creation and specification endpoints
- `api/settings.py` - Configuration with auto CORS for Agno playground

**Database Layer**
- `db/models.py` - SQLAlchemy models for dynamic agents, specifications, and knowledge bases
- `db/session.py` - Database session management and URL configuration
- `migrations/001_dynamic_agents.sql` - Database schema for dynamic agent system

**Core Systems**
- `core/provider_manager.py` - LLM provider abstraction (OpenAI, Anthropic, Google)
- `core/template_manager.py` - Agent specification templates
- `core/validation_system.py` - Agent specification validation
- `core/enhanced_tools.py` - Extended tool capabilities

### Key Features

**Dynamic Agent System** - Create agents at runtime with:
- Custom model configurations (OpenAI, Anthropic, Google)
- Tool selection (DuckDuckGo, YFinance, Reasoning, Knowledge)
- Memory and knowledge base integration
- Validation with quality scoring (0-100)
- Performance metrics tracking

**Agent Types** - Four predefined agents available:
- `web_agent` - Web search capabilities
- `finance_agent` - Stock data and financial analysis
- `agno_assist` - Help with Agno framework (requires knowledge base loading)
- `meta_agent_builder` - Creates other agents dynamically

## Environment Configuration

Required API keys in `.env`:
- `OPENAI_API_KEY` - For GPT models (default)
- `ANTHROPIC_API_KEY` - For Claude models 
- Database credentials (optional, defaults to Docker compose values)

## Database

PostgreSQL with pgvector extension for embeddings. Default development setup uses Docker compose. Production should use managed database services.

## Testing

Currently uses basic agent creation tests. Check `test_meta_agent.py` for examples.

## Dependencies Management

Uses `uv` for Python package management. Dependencies defined in `pyproject.toml`, with `requirements.txt` auto-generated for Docker builds.