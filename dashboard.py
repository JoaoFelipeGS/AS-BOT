"""
Dashboard de acompanhamento
"""

from datetime import datetime

import config
import utils
import database
import queue_manager

logger = utils.setup_logger("dashboard")

# =========================================================
# MENU PRINCIPAL
# =========================================================

def mostrar_menu():
    """Mostrar menu de opções"""
    
    print("\n" + "="*80)
    print("🤖 BOT DE PUBLICAÇÃO - MARKETPLACE FACEBOOK")
    print("="*80)
    
    opcoes = {
        "1": ("📦 Ver fila de publicações", mostrar_fila_detalhada),
        "2": ("📊 Estatísticas gerais", mostrar_estatisticas),
        "3": ("⏭️  Publicar próximo imóvel agora", lambda: print("Use o menu principal")),
        "4": ("❌ Remover item da fila", remover_item_menu),
        "5": ("⏰ Reprogramar publicação", reprogramar_menu),
        "6": ("🗑️  Limpar erros", limpar_erros_menu),
        "7": ("📜 Ver logs", ver_logs_menu),
        "8": ("🔄 Sair", lambda: None),
    }
    
    print("\nOpções:")
    for tecla, (descricao, _) in opcoes.items():
        print(f"  {tecla}. {descricao}")
    
    print("\n" + "-"*80)
    
    escolha = input("Escolha uma opção (1-8): ").strip()
    
    if escolha in opcoes:
        funcao = opcoes[escolha][1]
        if funcao:
            funcao()
        return escolha != "8"  # Return False se escolher sair
    else:
        print("❌ Opção inválida")
        return True  # Continuar no loop

# =========================================================
# FILA
# =========================================================

def mostrar_fila_detalhada():
    """Mostrar fila com detalhes"""
    
    queue_manager.mostrar_fila()

# =========================================================
# ESTATÍSTICAS
# =========================================================

def mostrar_estatisticas():
    """Mostrar estatísticas do bot"""
    
    print("\n" + "="*80)
    print("📊 ESTATÍSTICAS")
    print("="*80)
    
    try:
        with database.db.get_connection() as conn:
            cur = conn.cursor()
            
            # Total de imóveis
            cur.execute("SELECT COUNT(*) FROM imoveis;")
            total_imoveis = cur.fetchone()[0]
            
            # Total publicado
            cur.execute("""
                SELECT COUNT(*) FROM fila_publicacao
                WHERE status = 'publicado';
            """)
            total_publicado = cur.fetchone()[0]
            
            # Em fila
            cur.execute("""
                SELECT COUNT(*) FROM fila_publicacao
                WHERE status IN ('aguardando', 'processando');
            """)
            em_fila = cur.fetchone()[0]
            
            # Bloqueados
            cur.execute("""
                SELECT COUNT(*) FROM bloqueios
                WHERE desbloqueado_em IS NULL;
            """)
            bloqueados_agora = cur.fetchone()[0]
            
            # Taxa de sucesso
            if total_publicado + em_fila > 0:
                taxa = (total_publicado / (total_publicado + em_fila)) * 100
            else:
                taxa = 0
            
            print(f"\n📈 Números gerais:")
            print(f"   Total de imóveis: {total_imoveis}")
            print(f"   Publicados: {total_publicado}")
            print(f"   Na fila: {em_fila}")
            print(f"   Taxa de sucesso: {taxa:.1f}%")
            
            # Tempo médio na fila
            cur.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (publicado_em - criado_em)) / 3600)
                FROM fila_publicacao
                WHERE status = 'publicado' AND publicado_em IS NOT NULL;
            """)
            
            tempo_medio = cur.fetchone()[0]
            if tempo_medio:
                print(f"   Tempo médio na fila: {tempo_medio:.1f}h")
            
            # Bloqueios
            print(f"\n⚠️  Bloqueios:")
            print(f"   Ativos agora: {bloqueados_agora}")
            
            cur.execute("""
                SELECT tipo, COUNT(*) FROM bloqueios
                GROUP BY tipo
                ORDER BY COUNT(*) DESC;
            """)
            
            for tipo, count in cur.fetchall():
                print(f"   • {tipo}: {count}")
            
            # Imóveis mais novos
            print(f"\n🏠 Imóveis mais recentes:")
            cur.execute("""
                SELECT titulo, preco, criado_em FROM imoveis
                ORDER BY criado_em DESC
                LIMIT 5;
            """)
            
            for titulo, preco, criado_em in cur.fetchall():
                data_fmt = utils.formatar_data(criado_em)
                print(f"   • {titulo[:40]}")
                print(f"     R$ {preco:.0f} - {data_fmt}")
    
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        print(f"❌ Erro: {e}")
    
    print("\n" + "="*80 + "\n")
    input("Pressione ENTER para voltar")

# =========================================================
# GERENCIAMENTO
# =========================================================

def remover_item_menu():
    """Menu para remover item da fila"""
    
    print("\n" + "="*80)
    print("❌ REMOVER DA FILA")
    print("="*80)
    
    queue_manager.mostrar_fila()
    
    try:
        fila_id = int(input("ID da fila para remover: "))
        
        if queue_manager.remover_fila(fila_id):
            print("✓ Removido com sucesso")
        else:
            print("❌ Erro ao remover")
    
    except:
        print("❌ ID inválido")
    
    print("="*80 + "\n")

def reprogramar_menu():
    """Menu para reprogramar publicação"""
    
    print("\n" + "="*80)
    print("⏰ REPROGRAMAR")
    print("="*80)
    
    queue_manager.mostrar_fila()
    
    try:
        fila_id = int(input("ID da fila para reprogramar: "))
        horas = int(input(f"Horas até publicar (padrão {config.HORAS_ENTRE_PUBLICACOES}): ") or config.HORAS_ENTRE_PUBLICACOES)
        
        if queue_manager.reprogramar_fila(fila_id, horas):
            print("✓ Reprogramado com sucesso")
        else:
            print("❌ Erro ao reprogramar")
    
    except:
        print("❌ Entrada inválida")
    
    print("="*80 + "\n")

def limpar_erros_menu():
    """Menu para limpar erros"""
    
    print("\n" + "="*80)
    print("🗑️  LIMPAR ERROS")
    print("="*80)
    
    confirmacao = input("Remover todos os itens com 5+ erros? (S/N): ").strip().upper()
    
    if confirmacao == "S":
        if queue_manager.limpar_erros():
            print("✓ Itens removidos")
        else:
            print("❌ Erro ao limpar")
    else:
        print("Cancelado")
    
    print("="*80 + "\n")

# =========================================================
# LOGS
# =========================================================

def ver_logs_menu():
    """Ver logs recentes"""
    
    print("\n" + "="*80)
    print("📜 LOGS RECENTES")
    print("="*80)
    
    try:
        with database.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT tipo, mensagem, criado_em FROM logs
                ORDER BY criado_em DESC
                LIMIT 20;
            """)
            
            for tipo, mensagem, criado_em in cur.fetchall():
                data_fmt = utils.formatar_data(criado_em)
                emoji = "✓" if "sucesso" in tipo else "⚠️" if "erro" in tipo else "•"
                
                print(f"{emoji} [{tipo}] {data_fmt}")
                print(f"   {mensagem[:70]}")
    
    except Exception as e:
        logger.error(f"Erro ao ler logs: {e}")
        print(f"❌ Erro: {e}")
    
    print("="*80 + "\n")
    input("Pressione ENTER para voltar")

# =========================================================
# INICIAR
# =========================================================

def iniciar_dashboard():
    """Iniciar dashboard interativo"""
    
    while True:
        try:
            continuar = mostrar_menu()
            if not continuar:
                print("\nSaindo do dashboard...\n")
                break
        except KeyboardInterrupt:
            print("\n\nSaindo...")
            break
        except Exception as e:
            logger.error(f"Erro no dashboard: {e}")
            print(f"❌ Erro: {e}")
            input("Pressione ENTER para continuar")
