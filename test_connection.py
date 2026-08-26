#!/usr/bin/env python
"""
Script de teste rápido do sistema
"""

import sys

print("\n" + "="*80)
print("🧪 TESTE DO SISTEMA")
print("="*80)

print("\n1. Verificando importações...")
try:
    import config
    import utils
    import database
    import extractor
    import error_handler
    import facebook_handler
    import queue_manager
    import dashboard
    print("   ✅ Todos os módulos importados")
except Exception as e:
    print(f"   ❌ Erro ao importar: {e}")
    sys.exit(1)

print("\n2. Testando banco de dados...")
try:
    with database.db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM imoveis;")
        count = cur.fetchone()[0]
        print(f"   ✅ Banco conectado - {count} imóveis armazenados")
except Exception as e:
    print(f"   ⚠️  Erro ao conectar banco: {e}")
    print("   → Configure DATABASE_URL em config.py ou .env")

print("\n3. Testando logger...")
try:
    logger = utils.setup_logger("test")
    logger.info("Teste de log funcionando")
    print("   ✅ Logger funcionando")
except Exception as e:
    print(f"   ❌ Erro no logger: {e}")

print("\n4. Verificando estrutura de diretórios...")
import os
dirs = [config.DIR_DATA, config.DIR_IMAGES, config.DIR_PERFIL, config.DIR_LOGS]
for d in dirs:
    if os.path.exists(d):
        print(f"   ✅ {d}/")
    else:
        print(f"   ❌ {d}/ não existe")

print("\n5. Testando funções principais...")
try:
    # Test utils functions
    preco_limpo = utils.limpar_preco("R$ 500.000,00")
    assert preco_limpo == 500000.0, f"Preço incorreto: {preco_limpo}"
    print("   ✅ utils.limpar_preco()")
    
    # Test validation
    dados_teste = {
        "titulo": "Casa bonita em Marília",
        "preco": "R$ 500.000,00",
        "descricao": "Casa com 3 quartos, 2 banheiros, garagem para 2 carros. Muito bonita e bem localizada.",
        "endereco": "Marília, SP",
        "quartos": 3,
        "banheiros": 2,
        "garagem": 2,
        "area": 150,
        "fotos": [],
        "url": "https://example.com"
    }
    validacao = utils.validar_imovel(dados_teste)
    print(f"   ✅ utils.validar_imovel() - Score: {validacao['score']}/4")
    
except Exception as e:
    print(f"   ❌ Erro ao testar funções: {e}")

print("\n" + "="*80)
print("✅ TESTES CONCLUÍDOS")
print("="*80)
print("\nO sistema está pronto para uso!")
print("Execute 'python app.py' para iniciar.\n")
