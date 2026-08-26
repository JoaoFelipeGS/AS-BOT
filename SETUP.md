# INSTRUÇÕES DE SETUP

## 🚀 Instalação Rápida

### 1. Criar Conta no Neon (Banco de Dados PostgreSQL)

1. Acesse: https://console.neon.tech/
2. Crie uma conta gratuita
3. Crie um novo projeto
4. Copie a **CONNECTION STRING** (parecida com: `postgresql://user:password@ep-xxx.us-east-1.neon.tech/neondb`)

### 2. Configurar Variável de Ambiente

**Opção A: Windows (Recomendado)**

Crie um arquivo `.env` na pasta do bot:

```
DATABASE_URL=postgresql://seu_usuario:sua_senha@seu_host/seu_db
```

**Opção B: Editar config.py**

Abra `config.py` e altere:

```python
NEON_DATABASE_URL = "postgresql://seu_usuario:sua_senha@seu_host/seu_db"
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Executar o Bot

```bash
python app.py
```

---

## 📖 Como Usar

### Fluxo Básico

```
1. EXTRAÇÃO
   ↓
2. ARMAZENAGEM (Banco Neon)
   ↓
3. FILA (Agendamento automático)
   ↓
4. PUBLICAÇÃO (Manual + automático)
```

### Menu Principal

```
🤖 BOT DE PUBLICAÇÃO
════════════════════════════════════════════

Opções:
  1. 📥 Extrair imóveis da AS Imobiliária
  2. 📤 Publicar próximo imóvel
  3. 📦 Ver fila de publicações
  4. 📊 Ver dashboard
  5. 🚪 Sair
```

### 1️⃣ Extrair Imóveis

1. Escolha opção "1"
2. Navegue pelo site da AS Imobiliária normalmente
3. **CTRL + CLIQUE** nos imóveis que quer publicar
4. Pressione ENTER
5. Dados são extraídos e salvos no banco Neon

### 2️⃣ Publicar no Facebook

1. Escolha opção "2"
2. Bot abre Facebook Marketplace
3. Preenche ~80% dos dados automaticamente
4. **Você verifica e publica manualmente**
5. Próxima publicação agendada automaticamente

### 3️⃣ Gerenciar Fila

1. Escolha opção "3"
2. Veja status de todos os imóveis
3. Remove, reprograma ou limpa erros se necessário

### 4️⃣ Dashboard Avançado

1. Escolha opção "4"
2. Menu interativo com:
   - Estatísticas gerais
   - Histórico de bloqueios
   - Logs de operação
   - Gerenciamento manual da fila

---

## ⚠️ Tratamento de Bloqueios

### O que acontece se Facebook bloquear?

```
1. Bot detecta bloqueio automaticamente
2. Pausa todas as operações por 12-24h
3. Mostra mensagem ao usuário
4. Você pode resolver manualmente
5. Bot retoma após desbloqueio
```

### Como evitar bloqueios?

✅ **Limite:** Máx 3 anúncios por dia  
✅ **Intervalo:** Mínimo 3 horas entre publicações  
✅ **Comportamento:** Delays aleatórios (parece humano)  
✅ **Validação:** Dados completos em todos os anúncios  

❌ **NÃO FAÇA:**
- Publicar muitos anúncios rapidinho
- Usar dados ruins/duplicados
- Ignorar avisos de bloqueio
- Tentar burlar detecção Facebook

---

## 📚 Estrutura do Projeto

```
as_marketplace_bot_v2/
├── app.py                  # Menu principal
├── config.py               # Configurações
├── utils.py                # Funções auxiliares
├── database.py             # Neon PostgreSQL
├── extractor.py            # Extração de dados
├── error_handler.py        # Detecção de bloqueios
├── facebook_handler.py     # Publicação automática
├── queue_manager.py        # Fila de publicações
├── dashboard.py            # Dashboard interativo
├── requirements.txt        # Dependências Python
├── .env                    # Variáveis (não commitar)
├── data/
│   └── imoveis.json        # Backup local
├── images/                 # Fotos baixadas
├── logs/                   # Histórico de operações
└── perfil_playwright/      # Dados navegador persistentes
```

---

## 🔍 Diagnosticar Problemas

### Erro: "Não consegui conectar ao Neon"

```
✗ Verifique se:
  1. DATABASE_URL está configurada
  2. Conexão de internet ativa
  3. Credenciais corretas no Neon
  4. Firewall permite conexão
```

### Erro: "Nenhum imóvel selecionado"

```
✗ CTRL + CLIQUE não funcionou?
  1. Clique primeiro na página
  2. Depois CTRL + CLIQUE no imóvel
  3. Deve aparecer uma borda laranja
```

### Erro: "Imóvel inválido"

```
✗ Faltam dados obrigatórios:
  • Título (mínimo 5 caracteres)
  • Preço (mínimo R$ 1000)
  • Descrição (mínimo 50 caracteres)
  • Imagens (pelo menos 1)
```

### Facebook pedindo CAPTCHA?

```
1. Resolva o CAPTCHA manualmente
2. Faça login se necessário
3. Volte para o bot
4. Pressione ENTER
5. Bot continua automaticamente
```

---

## 🔐 Segurança

⚠️ **Nunca compartilhe sua CONNECTION STRING do Neon!**

```python
# ❌ ERRADO
DATABASE_URL = "postgresql://user:pass@host/db"  # Público

# ✅ CERTO
# Use variável de ambiente .env (não versionado no Git)
DATABASE_URL = os.getenv("DATABASE_URL")
```

---

## 📞 Dúvidas Frequentes

**P: Por que o bot não publica automaticamente tudo?**  
R: Facebook bloqueia contas que publicam muitos anúncios automaticamente. Nosso sistema pede confirmação manual para parecer humano e evitar bloqueio.

**P: Quanto custa?**  
R: Bot é gratuito. Neon oferece 3GB grátis de PostgreSQL (mais que suficiente).

**P: Posso usar com múltiplas contas Facebook?**  
R: Sim! Cada conta tem seu próprio navegador persistente. Basta alternar.

**P: E se a internet cair?**  
R: Dados estão salvos no Neon. Quando volta, retoma de onde parou.

**P: Funciona em Linux/Mac?**  
R: Sim! Mesmo código, só muda variável de ambiente.

---

## 🆘 Suporte

Se tiver problemas:

1. Verifique os **logs/** para mensagens de erro
2. Veja o **dashboard** para status da fila
3. Consulte este README
4. Revise a configuração do Neon

---

**Última atualização:** Maio 2026  
**Versão:** 2.0 (com Neon + Fila Automática)
