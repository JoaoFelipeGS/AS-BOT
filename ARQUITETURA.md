🏗️ ARQUITETURA DO BOT v2.0

════════════════════════════════════════════════════════════════════════════════

COMPONENTES PRINCIPAIS:

📱 app.py
   └─ Menu interativo principal
   └─ Orquestra todos os módulos
   └─ Gerencia fluxo de extração e publicação

⚙️ NÚCLEO DE DADOS:

   config.py
   └─ Configurações centralizadas
   └─ Delays, limites, timeouts
   └─ Variáveis de ambiente (Neon)

   database.py (Neon PostgreSQL)
   └─ Tabelas:
      • imoveis → Dados extraídos
      • fila_publicacao → Agendamento
      • bloqueios → Histórico de bloqueios
      • logs → Auditoria completa
   
   utils.py
   └─ Funções compartilhadas
   └─ Delays humanos, validações, formatação

📦 PIPELINE DE EXTRAÇÃO:

   extractor.py
   ├─ Abre página do imóvel
   ├─ Extrai: título, preço, descrição, endereço
   ├─ Extrai: quartos, banheiros, garagem, área
   ├─ Baixa imagens
   └─ Valida dados antes de salvar

🚀 PUBLICAÇÃO INTELIGENTE:

   facebook_handler.py
   ├─ Abre Facebook Marketplace
   ├─ Faz upload de imagens
   ├─ Preenche título, preço, descrição
   ├─ Valida antes de publicar
   └─ Registra publicação no banco

🚨 PROTEÇÃO CONTRA BLOQUEIOS:

   error_handler.py
   ├─ Detecta: Checkpoint, Login, CAPTCHA
   ├─ Detecta: Rate Limit, Atividade Suspeita
   ├─ Pausa automática se bloqueio
   ├─ Pede confirmação manual do usuário
   └─ Registra tudo no banco

📋 GERENCIAMENTO DE FILA:

   queue_manager.py
   ├─ Adiciona imóvel à fila
   ├─ Obtém próximo para publicar
   ├─ Reprograma publicações
   ├─ Remove itens com erro
   └─ Mostra status visual da fila

📊 INTERFACE:

   dashboard.py
   ├─ Menu interativo
   ├─ Estatísticas e gráficos
   ├─ Gerenciamento manual
   ├─ Logs estruturados
   └─ Bloqueios detectados

════════════════════════════════════════════════════════════════════════════════

FLUXO DE DADOS:

1. EXTRAÇÃO:
   
   Usuário clica (CTRL + CLIQUE)
              ↓
   app.py → extractor.py
              ↓
   Extrai dados (BeautifulSoup)
              ↓
   Valida dados (utils.py)
              ↓
   Salva em database.py (Neon)
              ↓
   Adiciona à fila (queue_manager.py)

2. AGENDAMENTO:

   database.py verifica hora
              ↓
   Se pronto → queue_manager.obter_proxima_publicacao()
              ↓
   Aguarda confirmação do usuário

3. PUBLICAÇÃO:

   facebook_handler.py abre Facebook
              ↓
   Detecta bloqueios (error_handler.py)
              ↓
   Se bloqueado → Pausa + pede manual
   Se OK → Preenche dados (80%)
              ↓
   Usuário valida e publica
              ↓
   database.py registra publicação
              ↓
   Próxima agendada (3h depois)

4. PROTEÇÃO:

   error_handler.py monitora continuamente
              ↓
   Detecta: Checkpoint, CAPTCHA, Rate Limit
              ↓
   Registra em bloqueios table
              ↓
   Pausa publicações por 12-24h
              ↓
   Usuário resolve manualmente
              ↓
   database.db.desbloquear()

════════════════════════════════════════════════════════════════════════════════

BANCO DE DADOS (NEON):

TABELA: imoveis
├─ id (serial primary key)
├─ url (unique)
├─ titulo, preco, descricao, endereco
├─ quartos, banheiros, garagem, area
├─ imagens_json (armazenado como JSON)
└─ timestamps

TABELA: fila_publicacao
├─ id, imovel_id (FK)
├─ status (aguardando, publicado, bloqueado, erro)
├─ agendado_para (próxima tentativa)
├─ publicado_em, tentativas
├─ url_facebook, mensagem_erro
└─ timestamps

TABELA: bloqueios
├─ id, tipo (checkpoint, captcha, rate_limit, etc)
├─ detectado_em, desbloqueado_em
├─ motivo, detalhes
└─ timestamps

TABELA: logs
├─ id, tipo (extracao, publicacao, erro, etc)
├─ mensagem, detalhes (JSON)
└─ timestamp

════════════════════════════════════════════════════════════════════════════════

DELAYS "HUMANOS":

• Entre cliques: 300-800ms
• Entre keystrokes: 50-150ms (por caractere)
• Entre ações: 1-4.5 segundos
• Scroll: aleatório 300-1200px
• Upload: 10-25 segundos

Objetivo: Parecer humano para Facebook não bloquear

════════════════════════════════════════════════════════════════════════════════

VALIDAÇÕES:

Antes de extrair:
 ✓ Página carregou (networkidle)?
 ✓ Há conteúdo para extrair?

Antes de publicar:
 ✓ Título 5-90 caracteres?
 ✓ Preço >= R$ 1000?
 ✓ Descrição 50+ caracteres?
 ✓ Pelo menos 1 imagem?
 ✓ Não há bloqueio ativo?
 ✓ Menos de 3 publicações hoje?
 ✓ Última publicação foi 3h atrás?

════════════════════════════════════════════════════════════════════════════════

LIMITES DE SEGURANÇA:

⏱️ Publicações por dia: 3 máximo
⏱️ Intervalo entre: 3+ horas
⏱️ Pausa após bloqueio: 12-24 horas
⏱️ Timeout carregamento: 2 minutos
⏱️ Timeout upload: 5 minutos

════════════════════════════════════════════════════════════════════════════════

LOGS E AUDITORIA:

Tudo registrado em:
 • database.py → logs table
 • /logs/*.log → arquivo local
 • Console → saída em tempo real

Possibilita rastreamento completo de:
 ✓ Extrações bem-sucedidas/falhadas
 ✓ Publicações realizadas
 ✓ Bloqueios detectados
 ✓ Erros e exceções

════════════════════════════════════════════════════════════════════════════════

PRÓXIMAS MELHORIAS POSSÍVEIS:

□ API REST para controle remoto
□ Integração com WhatsApp (notificações)
□ Suporte a múltiplas imobiliárias
□ Publicação em plataformas extras
□ Dashboard web (ao invés de terminal)
□ Backup automático de imagens
□ Rotação de accounts Facebook

════════════════════════════════════════════════════════════════════════════════
