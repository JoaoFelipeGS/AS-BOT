"""
Gerenciador de fila de publicações
"""

from datetime import datetime, timedelta

import config
import utils
import database

logger = utils.setup_logger("queue_manager")

# =========================================================
# ADICIONAR À FILA
# =========================================================

def adicionar_fila(imovel_id):
    """Adicionar imóvel à fila de publicação"""
    
    fila_id = database.db.adicionar_fila(imovel_id)
    
    if fila_id:
        logger.info(f"Imóvel {imovel_id} adicionado à fila")
        return fila_id
    
    logger.error(f"Falha ao adicionar fila para imóvel {imovel_id}")
    return None

# =========================================================
# GERENCIAR FILA
# =========================================================

def obter_proxima_publicacao():
    """Obter próximo imóvel agendado"""
    
    return database.db.obter_proxima_publicacao()

def obter_status_fila():
    """Obter estatísticas da fila"""
    
    return database.db.obter_fila_status()

def listar_fila(limite=10):
    """Listar imóveis na fila"""
    
    try:
        with database.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    f.id as fila_id,
                    i.id as imovel_id,
                    i.titulo,
                    i.preco,
                    f.status,
                    f.agendado_para,
                    f.tentativas
                FROM fila_publicacao f
                JOIN imoveis i ON f.imovel_id = i.id
                ORDER BY 
                    CASE 
                        WHEN f.status = 'aguardando' THEN 1
                        WHEN f.status = 'bloqueado' THEN 2
                        ELSE 3
                    END,
                    f.agendado_para ASC
                LIMIT %s;
            """, (limite,))
            
            return cur.fetchall()
    
    except Exception as e:
        logger.error(f"Erro ao listar fila: {e}")
        return []

# =========================================================
# DISPLAY
# =========================================================

def mostrar_fila():
    """Mostrar status da fila de forma visual"""
    
    print("\n" + "="*80)
    print("📦 FILA DE PUBLICAÇÕES")
    print("="*80)
    
    # =====================================================
    # ESTATÍSTICAS
    # =====================================================
    
    status = obter_status_fila()
    
    if not status:
        print("Nenhum item na fila")
        print("="*80 + "\n")
        return
    
    total = sum(status.values())
    
    print(f"\nTotal: {total} imóvel(is)")
    
    for estado, count in status.items():
        emoji = {
            "aguardando": "⏳",
            "bloqueado": "🚫",
            "publicado": "✅",
            "erro": "❌",
            "processando": "⚙️"
        }.get(estado, "•")
        
        print(f"  {emoji} {estado.capitalize()}: {count}")
    
    # =====================================================
    # PRÓXIMA PUBLICAÇÃO
    # =====================================================
    
    proxima = obter_proxima_publicacao()
    
    if proxima:
        _, imovel_id, titulo, preco, _, _, _ = proxima
        
        print(f"\n🎯 Próximo a publicar:")
        print(f"   Imóvel: {titulo[:50]}")
        print(f"   Preço: R$ {preco}")
    
    # =====================================================
    # ITENS NA FILA
    # =====================================================
    
    print(f"\n📋 Últimos itens na fila:")
    print("-" * 80)
    
    itens = listar_fila(5)
    
    if not itens:
        print("Fila vazia")
    else:
        for idx, item in enumerate(itens, 1):
            fila_id, imovel_id, titulo, preco, status_item, agendado_para, tentativas = item
            
            # Status emoji
            emoji_status = {
                "aguardando": "⏳",
                "bloqueado": "🚫",
                "publicado": "✅",
                "erro": "❌",
                "processando": "⚙️"
            }.get(status_item, "•")
            
            # Tempo até publicação
            if agendado_para:
                tempo_restante = agendado_para - datetime.now()
                if tempo_restante.total_seconds() > 0:
                    horas = int(tempo_restante.total_seconds() // 3600)
                    minutos = int((tempo_restante.total_seconds() % 3600) // 60)
                    tempo_str = f"em {horas}h {minutos}m"
                else:
                    tempo_str = "PRONTO"
            else:
                tempo_str = "N/A"
            
            print(f"{idx}. {emoji_status} {titulo[:40]}")
            print(f"   Preço: R${preco:.0f} | {status_item} | {tempo_str}")
            
            if tentativas > 0:
                print(f"   ⚠️  {tentativas} tentativa(s)")
            
            print()
    
    print("="*80 + "\n")

# =========================================================
# AÇÕES MANUAIS
# =========================================================

def remover_fila(fila_id):
    """Remover imóvel da fila"""
    
    try:
        with database.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM fila_publicacao WHERE id = %s;",
                (fila_id,)
            )
            
            logger.info(f"Imóvel removido da fila: {fila_id}")
            return True
    
    except Exception as e:
        logger.error(f"Erro ao remover da fila: {e}")
        return False

def reprogramar_fila(fila_id, horas=None):
    """Reprogramar publicação"""
    
    if horas is None:
        horas = config.HORAS_ENTRE_PUBLICACOES
    
    novo_agendamento = datetime.now() + timedelta(hours=horas)
    
    try:
        with database.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE fila_publicacao
                SET agendado_para = %s, atualizado_em = NOW()
                WHERE id = %s;
            """, (novo_agendamento, fila_id))
            
            logger.info(f"Fila {fila_id} reprogramada para {novo_agendamento}")
            return True
    
    except Exception as e:
        logger.error(f"Erro ao reprogramar: {e}")
        return False

def limpar_erros():
    """Limpar itens com muitos erros"""
    
    try:
        with database.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM fila_publicacao
                WHERE tentativas >= 5 AND status = 'erro';
            """)
            
            logger.info(f"Itens com erro removidos")
            return True
    
    except Exception as e:
        logger.error(f"Erro ao limpar: {e}")
        return False
