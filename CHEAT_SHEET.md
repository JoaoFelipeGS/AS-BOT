# 📌 CHEAT SHEET - Referência Rápida

## INICIAR

```bash
python app.py              # Inicia menu principal
python test_connection.py  # Testa sistema
```

## BANCO DE DADOS

```bash
# Configure em .env:
DATABASE_URL=postgresql://...

# Ou em config.py:
NEON_DATABASE_URL = "postgresql://..."
```

## MENU PRINCIPAL

```
1 - Extrair imóveis
2 - Publicar próximo
3 - Ver fila
4 - Dashboard
5 - Sair
```

## EXTRAÇÃO

1. Opção 1 no menu
2. CTRL + CLIQUE em cada imóvel
3. ENTER quando terminar
4. Escolha quais publicar (ex: 1,3,5)

## PUBLICAÇÃO

1. Opção 2 no menu
2. Confirme com S
3. Browser abre Facebook
4. Sistema preenche 80%
5. Você publica
6. ENTER no terminal

## DASHBOARD (Opção 4)

1 - Ver fila
2 - Estatísticas
3 - Não usar
4 - Remover item
5 - Reprogramar
6 - Limpar erros
7 - Ver logs
8 - Sair

## CONFIGURAÇÕES (config.py)

```python
HORAS_ENTRE_PUBLICACOES = 3        # Intervalo entre posts
MAX_ANUNCIOS_POR_DIA = 3           # Limite diário
PAUSAR_APOS_BLOQUEIO_HORAS = 12    # Pausa se bloqueado
```

## LOGS

Visualizar: `Dashboard → Opção 7`
Arquivo: `logs/bot_YYYYMMDD_HHMMSS.log`

## BANCO NEON

Tabelas:
- imoveis - Imóveis extraídos
- fila_publicacao - Agenda e histórico
- bloqueios - Bloqueios Facebook
- logs - Auditoria

## ERROS COMUNS

| Problema | Solução |
|----------|---------|
| Módulo não encontrado | `pip install -r requirements.txt` |
| Playwright não encontrado | `playwright install chromium` |
| Banco offline | Verificar DATABASE_URL em .env |
| Sem imagens | Certifique-se que extraiu com imagens |
| Facebook bloqueia | Use outra conta ou aguarde 24h |

## ARQUIVOS IMPORTANTES

- `app.py` - Menu principal
- `config.py` - Configurações
- `database.py` - Banco de dados
- `facebook_handler.py` - Publicação
- `extractor.py` - Extração
- `dashboard.py` - Interface
- `.env` - Variáveis de ambiente

## COMANDOS ÚTEIS

```bash
# Testar importações
python -c "import app; print('OK')"

# Ver logs
tail -f logs/*.log

# Limpar cache
rm -rf __pycache__

# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

## ESTRUTURA DE PASTAS

```
as_marketplace_bot_v2/
├── app.py
├── config.py
├── database.py
├── extractor.py
├── facebook_handler.py
├── error_handler.py
├── queue_manager.py
├── utils.py
├── dashboard.py
├── data/
├── images/
├── logs/
├── perfil_playwright/
└── .env (crie este)
```

## STATUS FILA

- ⏳ Aguardando - Agendado para publicar
- ✅ Publicado - Já foi publicado
- 🚫 Bloqueado - Facebook bloqueou
- ❌ Erro - Falhou na publicação
- ⚙️ Processando - Em andamento

## BLOQUEIOS DETECTADOS

- checkpoint_ou_login - Precisa fazer login
- captcha - CAPTCHA do Facebook
- rate_limit - Muitas requisições
- atividade_suspeita - Comportamento anormal

## QUICK START (30 segundos)

```bash
# 1. Instale
pip install -r requirements.txt
playwright install chromium

# 2. Configure
echo "DATABASE_URL=postgresql://..." > .env

# 3. Teste
python test_connection.py

# 4. Execute
python app.py
```

## PERFORMANCE

- Extrair 10 imóveis: ~5-10 minutos
- Publicar 1 imóvel: ~3-5 minutos
- Limite: 3 por dia (segurança)
- Intervalo: 3 horas entre posts

---

**Última atualização:** 21/05/2026
**Status:** ✅ 100% Funcional
