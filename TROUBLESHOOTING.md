# 🔧 TROUBLESHOOTING TÉCNICO

## Problema: Módulo psycopg2 não encontrado

**Erro:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solução:**
```bash
# Instale novamente
pip install psycopg2-binary

# Ou em alguns sistemas
pip install psycopg2
```

---

## Problema: Playwright não encontrado

**Erro:**
```
playwright not found in PATH
```

**Solução:**
```bash
# Instale o browser
playwright install chromium

# Ou em powershell
python -m playwright install chromium
```

---

## Problema: Conexão PostgreSQL falha

**Erro:**
```
psycopg2.OperationalError: could not connect to server
```

**Causas e soluções:**

1. **DATABASE_URL incorreto**
```python
# Verificar em config.py
# Formato correto:
# postgresql://usuario:senha@host:porta/banco

# ❌ ERRADO:
DATABASE_URL = "postgresql://user:password@ep-xxx.us-east-1.neon.tech/neondb"

# ✅ CORRETO:
DATABASE_URL = "postgresql://seu_usuario:sua_senha@ep-xxxxx.us-east-1.neon.tech/neondb"
```

2. **Neon desligou instância**
- Acesse console.neon.tech
- Verifique status do projeto
- Clique em "Resume" se estiver pausado

3. **Firewall bloqueando**
```bash
# Teste conexão
psql -U usuario -h ep-xxxxx.us-east-1.neon.tech -d neondb

# Se pedir senha, significa conectou
```

---

## Problema: Facebook não abre no browser

**Erro:**
```
TimeoutError: Timeout waiting for page.goto()
```

**Soluções:**

1. **Verificar conexão internet**
```bash
ping facebook.com
```

2. **Chrome não está instalado**
```bash
# Reinstalar Playwright
playwright install chromium
```

3. **Porta bloqueada ou Chrome em uso**
```bash
# Fechar Chrome
taskkill /F /IM chrome.exe

# Então tente novamente
python app.py
```

---

## Problema: Imagens não baixam

**Erro:**
```
Erro imagem https://...jpg: [Errno 11001] getaddrinfo failed
```

**Soluções:**

1. **URL da imagem inválida**
- Verifique em `logs/bot_*.log`
- Algumas imagens podem estar com acesso negado

2. **Espaço em disco insuficiente**
```bash
# Verificar espaço
dir c:\

# Limpar pasta images se necessário
rmdir /S images
```

3. **Permissão negada**
```bash
# Dar permissão em windows
# Clique direito em pasta → Propriedades → Segurança
```

---

## Problema: Fila não atualiza

**Sintomas:**
- Mesmos imóveis aparecem toda vez
- Status não muda

**Soluções:**

1. **Banco não está salvando**
```bash
# Teste conexão
python test_connection.py
```

2. **Função atualizar_fila_status não é chamada**
- Verifique facebook_handler.py linha ~250
- Certifique que sucesso=True ao final

3. **Timestamp incorreto**
```python
# Verificar em config.py
HORAS_ENTRE_PUBLICACOES = 3

# Se 0, próximo fica para agora sempre
# Mude para 3 ou mais
```

---

## Problema: Sistema lento

**Sintomas:**
- Tudo demora muito
- Travamentos frequentes

**Soluções:**

1. **Reduzir delays**
```python
# Em config.py, reduzir
DELAY_MIN = 0.5  # de 1.0
DELAY_MAX = 2.0  # de 4.5
```

2. **Aumentar timeouts**
```python
TIMEOUT_CARREGAMENTO = 180000  # 3 min
TIMEOUT_UPLOAD = 600000  # 10 min
```

3. **Chrome usando muita memória**
- Fecha abas desnecessárias
- Reinicia PC se preciso

---

## Problema: Extrator não acha dados

**Sintomas:**
- Título = "Imóvel"
- Preço = 0
- Descrição vazia

**Diagnóstico:**

1. **Página não carregou completamente**
```python
# Em extractor.py linha ~20
wait_until="domcontentloaded"  # Mudar para
wait_until="networkidle"       # Mais seguro
```

2. **Estrutura HTML mudou**
- Site pode ter redesenhado
- Seletores CSS não funcionam mais
- Solução: atualizar seletores em extractor.py

3. **Proteção do site contra bot**
- Alguns sites bloqueiam scrapers
- Adicionar header User-Agent

---

## Problema: Publicação falha no Facebook

**Erro:**
```
❌ FALHOU - Falha preenchimento
```

**Causas:**

1. **Campos não encontrados**
```python
# Facebook mudou HTML
# Atualizar seletores em facebook_handler.py

# Achar novo seletor:
# F12 → Inspector → Procurar campo
# Copiar path ou class
```

2. **Checkpoint/Bloqueio**
```
Se vir mensagem de checkbox ou login:
→ Resolva manualmente
→ Pressione ENTER no terminal
→ Sistema automaticamente detecta
```

3. **Tipo de conta não permitida**
- Some contas FB não têm Marketplace
- Use outra conta
- Ou ativar em Configurações

---

## Problema: Erro 429 (Rate Limit)

**Erro:**
```
429: Too Many Requests
rate limit
```

**Solução:**
```python
# Em config.py, aumentar intervalo
HORAS_ENTRE_PUBLICACOES = 6  # de 3
MAX_ANUNCIOS_POR_DIA = 2     # de 3
DELAY_MIN = 3.0              # de 1.0
DELAY_MAX = 8.0              # de 4.5
```

---

## Problema: Especificar ambiente Python

**Se tiver múltiplas versões de Python:**

```bash
# Verificar qual Python está sendo usado
python --version

# Usar versão específica
python3 app.py          # Se tem Python 3
python3.11 app.py       # Versão específica

# Ou criar ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python app.py
```

---

## Problema: Variáveis de ambiente não carregam

**Erro:**
```
DATABASE_URL="postgresql://..." não reconhecida
```

**Solução:**

1. **Criar .env na pasta correta**
```bash
# Deve estar em:
c:\Users\Manuela\Desktop\as_marketplace_bot_v2\.env

# NÃO em:
c:\Users\Manuela\.env
```

2. **Formato correto do .env**
```
# Sem aspas!
DATABASE_URL=postgresql://usuario:senha@host/db

# Sem espaços!
DATABASE_URL=postgresql://...

# Não usar export
# NÃO: export DATABASE_URL=...
```

3. **Recarregar variáveis**
```bash
# Fechar terminal
# Abrir nova janela (força reload)
python app.py
```

---

## Problema: LOG enorme, muitos erros

**Solução:**

1. **Limpar arquivo de log**
```bash
# Deletar log antigo
del logs\*.log

# Sistema cria novo log na próxima execução
```

2. **Reduzir verbosidade**
```python
# Em config.py
LOG_LEVEL = "ERROR"  # de "INFO"
# Só mostra erros críticos
```

---

## Problema: Extrair dados: "JSON decode error"

**Erro:**
```
json.JSONDecodeError: Expecting value: line 1 column 1
```

**Solução:**
- Página retornou HTML inválido
- Pode estar com login requerido
- Verificar se site AS está online

---

## Debug Avançado

### Ativar modo verbose

```python
# No início de app.py, adicione:
import logging
logging.basicConfig(level=logging.DEBUG)

# Mais detalhes nos logs
```

### Inspecionar objeto página

```python
# Em qualquer função async:
html = await page.content()
print(html)  # Vê HTML completo

# Ou salvar em arquivo
with open('debug.html', 'w') as f:
    f.write(html)

# Abre debug.html no navegador
```

### Pausar execução para debug

```python
# Adicione em qualquer lugar:
import pdb; pdb.set_trace()

# Execução para, você pode debugar
# Comandos: n (próxima), c (continua), p variavel
```

---

## Checklist de Debug

- [ ] `python test_connection.py` passa?
- [ ] DATABASE_URL está em .env?
- [ ] Chrome/Chromium instalado?
- [ ] Logs mostram informações úteis?
- [ ] Banco PostgreSQL está online?
- [ ] Firewall permite conexão?
- [ ] Facebook account tem permissão Marketplace?

---

## Contato Neon (Banco de Dados)

Se banco offline:
- https://console.neon.tech
- Status: Verifique se projeto está rodando
- Logs: Console do Neon
- Suporte: support.neon.tech

---

## Contato Facebook

Se bloqueado:
- https://www.facebook.com/help
- Buscar: "Facebook Marketplace"
- Opção: "Solicitar revisão de conta"
- Aguardar 24-48h

---

**Última atualização:** 21/05/2026
**Status:** Documento técnico v1.0
