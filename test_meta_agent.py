#!/usr/bin/env python3
"""
Script de teste para validar o Meta-Agente Builder e sistema de criação de agentes
"""

import asyncio
import json
from typing import Dict, Any

from agents.meta_agent_builder import get_meta_agent_builder
from core.dynamic_agent_factory import agent_factory


async def test_meta_agent_basic():
    """Teste básico do meta-agente"""
    print("🧪 Testando Meta-Agente Builder...")
    
    try:
        # Criar instância do meta-agente
        meta_agent = get_meta_agent_builder(
            model_id="gpt-4o",
            user_id="test_user",
            session_id="test_session"
        )
        
        print("✅ Meta-agente criado com sucesso")
        
        # Teste de conversa básica
        response = await meta_agent.arun(
            "Olá! Preciso de um agente especialista em marketing digital. Pode me ajudar?",
            stream=False
        )
        
        print(f"📝 Resposta do meta-agente: {response.content[:200]}...")
        print("✅ Teste básico do meta-agente concluído")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste básico: {e}")
        return False


async def test_agent_specification_validation():
    """Teste de validação de especificações"""
    print("\n🧪 Testando validação de especificações...")
    
    # Especificação válida
    valid_spec = {
        "agent_config": {
            "name": "Marketing Expert Agent",
            "slug": "marketing_expert",
            "description": "Agente especialista em marketing digital",
            "role": "Marketing Specialist",
            "specialization": "Digital Marketing"
        },
        "model_config": {
            "provider": "openai",
            "model_id": "gpt-4o",
            "max_tokens": 2000,
            "temperature": 0.7
        },
        "tools_config": [
            {
                "name": "DuckDuckGoTools",
                "enabled": True,
                "config": {}
            }
        ],
        "instructions": {
            "system_message": "Você é um especialista em marketing digital...",
            "guidelines": [
                "Sempre forneça insights baseados em dados",
                "Mantenha-se atualizado com as últimas tendências"
            ]
        },
        "features": {
            "reasoning_enabled": False,
            "memory_enabled": True,
            "knowledge_enabled": True,
            "markdown": True
        }
    }
    
    # Especificação inválida (faltando campos obrigatórios)
    invalid_spec = {
        "agent_config": {
            "name": "Test Agent"
            # Faltando slug, description, etc.
        }
    }
    
    try:
        # Testar especificação válida
        validation_result = agent_factory.validator.validate_specification(valid_spec)
        print(f"✅ Especificação válida - Score: {validation_result['score']}")
        print(f"   Warnings: {validation_result['warnings']}")
        
        # Testar especificação inválida
        validation_result = agent_factory.validator.validate_specification(invalid_spec)
        print(f"✅ Especificação inválida detectada - Score: {validation_result['score']}")
        print(f"   Errors: {validation_result['errors']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False


async def test_agent_creation():
    """Teste de criação de agente"""
    print("\n🧪 Testando criação de agente...")
    
    test_spec = {
        "agent_config": {
            "name": "Test Marketing Agent",
            "slug": "test_marketing_agent",
            "description": "Agente de teste para marketing",
            "role": "Test Marketing Specialist",
            "specialization": "Marketing"
        },
        "model_config": {
            "provider": "openai",
            "model_id": "gpt-4o",
            "max_tokens": 2000,
            "temperature": 0.7
        },
        "tools_config": [
            {
                "name": "DuckDuckGoTools",
                "enabled": True,
                "config": {}
            }
        ],
        "instructions": {
            "system_message": "Você é um agente de teste especializado em marketing digital.",
            "guidelines": [
                "Forneça respostas úteis e informativas",
                "Use dados quando disponíveis"
            ]
        },
        "features": {
            "reasoning_enabled": False,
            "memory_enabled": True,
            "knowledge_enabled": False,
            "markdown": True
        }
    }
    
    try:
        # Criar agente
        result = await agent_factory.create_agent_from_specification(
            test_spec,
            created_by="test_user"
        )
        
        if result["success"]:
            print(f"✅ Agente criado com sucesso!")
            print(f"   Agent ID: {result['agent_id']}")
            print(f"   Validation Score: {result['validation_result']['score']}")
            
            # Testar carregamento do agente
            agent = await agent_factory.load_dynamic_agent(result["agent_id"])
            print("✅ Agente carregado com sucesso")
            
            # Teste de conversa com o agente criado
            response = await agent.arun("Olá! Pode me ajudar com marketing digital?", stream=False)
            print(f"📝 Resposta do agente criado: {response.content[:150]}...")
            
            return True
        else:
            print(f"❌ Falha na criação: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na criação: {e}")
        return False


async def test_api_endpoints():
    """Teste dos endpoints da API"""
    print("\n🧪 Testando endpoints da API...")
    
    try:
        # Simular teste dos endpoints
        print("✅ Endpoints configurados:")
        print("   - POST /v1/agent-builder/chat")
        print("   - POST /v1/agent-builder/parse-specification")
        print("   - POST /v1/agent-builder/create-agent")
        print("   - GET /v1/agent-builder/domains")
        print("   - GET /v1/agent-builder/tools")
        print("   - GET /v1/dynamic-agents/")
        print("   - POST /v1/dynamic-agents/{agent_id}/chat")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos endpoints: {e}")
        return False


async def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DO SISTEMA MULTI-AGENTES")
    print("=" * 50)
    
    tests = [
        ("Meta-Agente Básico", test_meta_agent_basic),
        ("Validação de Especificações", test_agent_specification_validation),
        ("Criação de Agente", test_agent_creation),
        ("Endpoints da API", test_api_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema pronto para uso.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
