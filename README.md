
# 🤖 Bot de Publicação Automática - Facebook Marketplace

Automação robusta para publicar anúncios de imóveis no Facebook Marketplace a partir da AS Imobiliária.

**Versão:** 2.0 (Com Neon PostgreSQL + Fila Automática)

---

## ✨ O Que é Novo na v2.0

- ✅ **Banco de Dados Neon** - Rastreamento persistente de imóveis
- ✅ **Fila Automática** - Agendamento inteligente de publicações
- ✅ **Detecção de Bloqueios** - Pausa automática se Facebook bloqueia
- ✅ **Dashboard Avançado** - Gerenciamento visual da fila
- ✅ **Logs Estruturados** - Histórico completo de operações
- ✅ **Validação Robusta** - Garante dados completos antes de publicar
- ✅ **Publicação Semi-Automática** - 80% automático + confirmação manual

---

## 📋 Requisitos

- **Python 3.8+**
- **Neon Account** (PostgreSQL gratuito) - https://console.neon.tech/
- **Facebook Account** (com permissão Marketplace)
- **Chrome/Chromium Browser**

---

## 🚀 Setup Rápido

### 1. Clone/Extraia o Projeto

```bash
cd as_marketplace_bot_v2
```

### 2. Crie Conta Neon

1. Acesse https://console.neon.tech/
2. Crie um novo projeto
3. Copie a **CONNECTION STRING**

### 3. Configure Variável de Ambiente

Crie arquivo `.env`:

```
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/neondb
```

Ou edite `config.py` diretamente.

### 4. Instale Dependências

```bash
pip install -r requirements.txt
playwright install chromium
```

### 5. Execute o Bot

```bash
python app.py
```

---

## 🎮 Como Usar

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

### Passo 1: Extrair Imóveis

```
1. Escolha opção "1"
2. Navegue pela AS Imobiliária
3. CTRL + CLIQUE nos imóveis desejados
4. Pressione ENTER
5. Dados salvos automaticamente no Neon
```

### Passo 2: Publicar

```
1. Escolha opção "2"
2. Bot abre Facebook Marketplace
3. Preenche dados (título, preço, descrição, imagens)
4. Você valida e clica PUBLICAR no Facebook
5. Próxima publicação agendada para 3h depois
```

### Passo 3: Gerenciar Fila

```
1. Escolha opção "3" ou "4"
2. Veja status de todos os imóveis
3. Remova, reprograme ou limpe erros conforme necessário
```

---

## 🛡️ Proteção Contra Bloqueios

O sistema detecta automaticamente:

- **Checkpoint/Login** → Pausa e pede confirmação manual

---

## 🧩 Nova Arquitetura SaaS

Este projeto agora inclui uma plataforma web profissional com backend e frontend separados:

- `backend/` — FastAPI, WebSocket em tempo real, serviços de extração e publicação, banco compatível SQLite/PostgreSQL.
- `frontend/` — React + Vite + Tailwind, painel SaaS, cards de imóveis, logs ao vivo e seleção visual.

### Inicializar a nova plataforma

1. Instale dependências Python:

```bash
pip install -r requirements.txt
```

2. Instale dependências do frontend:

```bash
cd frontend
npm install
```

3. Execute backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

4. Execute frontend:

```bash
npm run dev
```

- **CAPTCHA** → Pausa até usuário resolver
- **Rate Limit** → Pausa 12-24h automaticamente
- **Atividade Suspeita** → Alerta ao usuário

### Limites Seguros

- **Máx 3 anúncios por dia**
- **Intervalo de 3+ horas entre publicações**
- **Delays aleatórios** (parecem humanos)
- **Dados validados** antes de publicar

---

## 📁 Estrutura

```
as_marketplace_bot_v2/
├── app.py              # Menu principal
├── config.py           # Configurações centralizadas
├── utils.py            # Funções compartilhadas
├── database.py         # Gerenciador Neon PostgreSQL
├── extractor.py        # Extração de dados
├── error_handler.py    # Detecção de bloqueios
├── facebook_handler.py # Publicação no Facebook
├── queue_manager.py    # Fila de publicações
├── dashboard.py        # Dashboard interativo
├── requirements.txt    # Dependências Python
├── data/
│   └── imoveis.json    # Backup local (JSON)
├── images/             # Imagens baixadas
├── logs/               # Histórico de operações
└── perfil_playwright/  # Dados navegador persistentes
```

---

## 🔧 Configurações

Edite `config.py` para ajustar:

```python
# Delays (segundos)
DELAY_MIN = 1.0
DELAY_MAX = 4.5

# Horas entre publicações
HORAS_ENTRE_PUBLICACOES = 3

# Máximo por dia
MAX_ANUNCIOS_POR_DIA = 3

# Pausa após bloqueio (horas)
PAUSAR_APOS_BLOQUEIO_HORAS = 12
```

---

## 📊 Dashboard

Acesse opção "4" para:

- 📈 **Estatísticas** - Total publicados, na fila, etc
- 📋 **Fila Detalhada** - Status de cada imóvel
- 🗂️ **Gerenciamento** - Remover, reprogramar, limpar
- 📜 **Logs** - Histórico completo de operações

---

## ⚠️ Aviso Importante

- **Não publique muitos anúncios rapidinho** - Facebook bloqueia
- **Use dados reais e completos** - Evita erros
- **Resolva CAPTCHAs manualmente** - Bot pausará e esperará
- **Não compartilhe CONNECTION STRING** - Dados sensíveis
- **Respeite limites diários** - Máx 3 anúncios/dia

---

## 🔍 Troubleshooting

**Erro: "Não consegui conectar ao Neon"**
```
→ Verifique DATABASE_URL em config.py ou .env
→ Teste conexão em https://console.neon.tech/
```

**Erro: "Nenhum imóvel selecionado"**
```
→ Clique na página ANTES de CTRL + CLIQUE
→ Deve aparecer borda laranja no imóvel
```

**Facebook pedindo CAPTCHA?**
```
→ Resolva manualmente
→ Pressione ENTER no bot
→ Bot continua automaticamente
```

**Bloqueado por Facebook?**
```
→ Bot pausará 12-24h automaticamente
→ Aguarde e tente novamente depois
→ Ou use outra conta do Facebook
```

---

## 📚 Mais Informações

Leia [SETUP.md](SETUP.md) para:
- Instruções detalhadas de instalação
- FAQ - Perguntas frequentes
- Guia de segurança
- Troubleshooting avançado

---

## 📝 Licença

Uso pessoal/educacional. Respeite Termos de Serviço do Facebook.

---

## 🤝 Contribuições

Melhorias são bem-vindas! Abra uma issue ou pull request.

---

**Última atualização:** Maio 2026  
**Status:** Ativo e testado ✅
