📚 GUIA PASSO-A-PASSO

════════════════════════════════════════════════════════════════════════════════

EXEMPLO COMPLETO: Do início até publicação

════════════════════════════════════════════════════════════════════════════════

⏱️ TEMPO TOTAL: ~15 minutos (incluindo setup)

════════════════════════════════════════════════════════════════════════════════

PARTE 1: SETUP INICIAL (5 minutos) ⚙️

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 1: Neon Account                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

1. Abra: https://console.neon.tech/
2. Clique "Sign Up"
3. Use email + crie senha
4. Confirme email
5. Dashboard abre
6. Clique "Create Project"
7. Dê um nome (ex: "imobiliaria-bot")
8. Clique "Create"

Resultado: Você tem um banco PostgreSQL gratuito!

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 2: Copiar Connection String                                           │
└─────────────────────────────────────────────────────────────────────────────┘

1. Na dashboard do Neon, vá para "Connection strings"
2. Selecione a aba "Psycopg"
3. Copie o texto inteiro (começa com "postgresql://")
4. Guarde em um bloco de notas

Exemplo:
postgresql://neondb_owner:Abc123xyz@ep-small-123.us-east-1.neon.tech/neondb

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 3: Configurar Bot                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

1. Abra PowerShell
2. cd c:\Users\Manuela\Desktop\as_marketplace_bot_v2
3. Crie arquivo ".env":

   notepad .env

4. Cole no arquivo:

   DATABASE_URL=postgresql://neondb_owner:Abc123xyz@ep-small-123.us-east-1.neon.tech/neondb

5. Salve (Ctrl + S)

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 4: Instalar Dependências                                              │
└─────────────────────────────────────────────────────────────────────────────┘

PowerShell:

pip install -r requirements.txt
playwright install chromium

⏳ Aguarde terminar (pode demorar alguns minutos)

════════════════════════════════════════════════════════════════════════════════

PARTE 2: PRIMEIRA EXECUÇÃO (10 minutos) 🚀

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 5: Iniciar Bot                                                        │
└─────────────────────────────────────────────────────────────────────────────┘

PowerShell:

python app.py

Resultado esperado:

╔════════════════════════════════════════════════════════════════╗
║                 🤖 BOT DE PUBLICAÇÃO                          ║
║          FACEBOOK MARKETPLACE                                  ║
╚════════════════════════════════════════════════════════════════╝

✓ Conectando ao banco Neon...
✓ Banco de dados configurado
✓ Browser Playwright pronto

════════════════════════════════════════════════════════════════

✓ TUDO PRONTO! Iniciando...

════════════════════════════════════════════════════════════════


🤖 BOT DE PUBLICAÇÃO
════════════════════════════════════════════

Opções:
  1. 📥 Extrair imóveis da AS Imobiliária
  2. 📤 Publicar próximo imóvel
  3. 📦 Ver fila de publicações
  4. 📊 Ver dashboard
  5. 🚪 Sair

────────────────────────────────────────────

Escolha uma opção (1-5): 

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 6: Extrair Imóveis                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

1. Digite: 1
2. Pressione Enter

Resultado: Navegador abre com AS Imobiliária

   ════════════════════════════════════════════
   📦 MODO EXTRAÇÃO
   ════════════════════════════════════════════
   
   Instruções:
   1. Navegue pela AS Imobiliária normalmente
   2. CTRL + CLIQUE nos imóveis que você quer publicar
   3. Ao terminar, pressione ENTER
   ════════════════════════════════════════════

3. Navegue normalmente no site da AS Imobiliária
4. Encontre imóveis que quer publicar
5. Segure CTRL e clique no imóvel
   → Deve aparecer uma borda laranja ao redor
6. Repita para todos os imóveis (3-5 é uma boa quantidade)
7. Volta ao PowerShell
8. Pressione ENTER

⏳ Bot iniciará extração de cada imóvel...

Resultado esperado por imóvel:

   [1/3] Processando...
   Extraindo: https://www.asimobiliaria.com/imovel/12345
   ✓ Imagens salvas: 8
   ✓ Adicionado à fila (ID: 5)
   
   [2/3] Processando...
   ...

Final:

   ════════════════════════════════════════════
   ✓ EXTRAÇÃO CONCLUÍDA
     • 3 imóvel(is) adicionado(s)
   ════════════════════════════════════════════

════════════════════════════════════════════════════════════════════════════════

PARTE 3: PUBLICAÇÃO (15+ minutos) 📤

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 7: Ver Fila                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

Voltou ao menu? Escolha opção 3:

   Escolha uma opção (1-5): 3

Resultado:

   ════════════════════════════════════════════════════════════════════════════
   📦 FILA DE PUBLICAÇÕES
   ════════════════════════════════════════════════════════════════════════════
   
   Total: 3 imóvel(is)
   
     ⏳ aguardando: 3
     ✅ publicado: 0
     ❌ erro: 0
   
   🎯 Próximo a publicar:
      Imóvel: Casa Alto Padrão - 3 quartos, 2 banheiros
      Preço: 450000.0
   
   📋 Últimos itens na fila:
   ────────────────────────────────────────────────────────────────────────────
   1. ⏳ Casa Alto Padrão - 3 quartos, 2 banheiros
      Preço: R$450000 | aguardando | PRONTO
   
   2. ⏳ Apartamento Moderno - 2 quartos, 1 banheiro
      Preço: R$280000 | aguardando | em 3h 0m
   
   3. ⏳ Terreno Comercial - Sem quartos
      Preço: R$150000 | aguardando | em 6h 0m
   
   ════════════════════════════════════════════════════════════════════════════

✅ Ótimo! Você tem 3 imóveis aguardando.

O PRIMEIRO está pronto para publicar agora!

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 8: Publicar Primeiro Imóvel                                           │
└─────────────────────────────────────────────────────────────────────────────┘

Voltou ao menu? Escolha opção 2:

   Escolha uma opção (1-5): 2

Resultado:

   ════════════════════════════════════════════
   📤 MODO PUBLICAÇÃO
   ════════════════════════════════════════════
   
   Próximo: Casa Alto Padrão - 3 quartos, 2 banheiros
   Preço: R$ 450000
   
   Publicar agora? (S/N): S

⏳ Bot inicia automático:
   1. Abre Facebook Marketplace
   2. Faz login (se necessário)
   3. Faz upload das imagens (8 imagens)
   4. Preenche título, preço, descrição
   5. Aguarda você clicar PUBLICAR

📋 Você vê na tela:

   ════════════════════════════════════════════
   REVISE OS DADOS NO FACEBOOK
   ════════════════════════════════════════════
   
   📌 Casa Alto Padrão - 3 quartos, 2 banheiros
   💰 450000
   📍 Marília, SP - Bairro Centro
   
   Casa Alto Padrão
   
   Localizada em Marília, SP. Imóvel novo, acabado, com
   3 quartos espaçosos, 2 banheiros, cozinha moderna, sala
   ampla, garagem para 2 carros...
   
   ════════════════════════════════════════════
   Se tudo estiver correto, clique em PUBLICAR no Facebook
   Depois pressione ENTER aqui
   ════════════════════════════════════════════

✅ Você agora:

   1. Verifica os dados no Facebook
   2. Ajusta se necessário (descrição, preço, etc)
   3. Clica o botão PUBLICAR do Facebook
   4. Volta ao PowerShell
   5. Pressione ENTER

⏳ Bot registra:

   ✓ Imóvel publicado com sucesso!

📅 Próxima publicação agendada:
   • Próximo imóvel em 3 horas
   • Você não precisa fazer nada!
   • Pode fechar o bot e voltar depois

════════════════════════════════════════════════════════════════════════════════

PARTE 4: PRÓXIMAS PUBLICAÇÕES 🔄

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 9: Próximas Tentativas                                                │
└─────────────────────────────────────────────────────────────────────────────┘

Você pode:

A) Fechar o bot agora
   • Dados estão salvos no Neon
   • Daqui a 3h, execute de novo
   • Próximo imóvel estará pronto

B) Continuar no menu:
   • Digite 2 novamente
   • Bot diz "Nenhum imóvel pronto agora"
   • Você pode escolher 3 para ver fila
   • Ou sair (opção 5)

════════════════════════════════════════════════════════════════════════════════

PARTE 5: GERENCIAR DEPOIS 📊

┌─────────────────────────────────────────────────────────────────────────────┐
│ PASSO 10: Dashboard Avançado                                                │
└─────────────────────────────────────────────────────────────────────────────┘

Execute bot: python app.py

Escolha opção 4:

   Escolha uma opção (1-5): 4

Menu interativo aparece:

   🤖 BOT DE PUBLICAÇÃO
   ════════════════════════════════════════════
   
   Opções:
     1. 📦 Ver fila de publicações
     2. 📊 Estatísticas gerais
     3. ⏭️  Publicar próximo imóvel agora
     4. ❌ Remover item da fila
     5. ⏰ Reprogramar publicação
     6. 🗑️  Limpar erros
     7. 📜 Ver logs
     8. 🔄 Sair

Exemplo: Você quer remover um imóvel:

   Escolha: 4
   
   ❌ REMOVER DA FILA
   
   (mostra fila)
   
   ID da fila para remover: 2
   
   ✓ Removido com sucesso

════════════════════════════════════════════════════════════════════════════════

⚠️ CENÁRIOS ESPECIAIS

┌─────────────────────────────────────────────────────────────────────────────┐
│ CENÁRIO 1: Facebook Pedindo CAPTCHA                                         │
└─────────────────────────────────────────────────────────────────────────────┘

Bot mostra:

   🤖 CAPTCHA DETECTADO
   
   Facebook está pedindo para resolver um CAPTCHA.
   
   1. Resolva o CAPTCHA
   2. Pressione ENTER aqui quando terminar

✅ Você faz:

   1. Resolve o CAPTCHA manualmente (clicando números, etc)
   2. Volta ao PowerShell
   3. Pressione ENTER
   4. Bot continua automaticamente!

┌─────────────────────────────────────────────────────────────────────────────┐
│ CENÁRIO 2: Facebook Bloqueia (Rate Limit)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

Bot detecta e mostra:

   ⏸️ LIMITE DE TAXA ATINGIDO
   
   Facebook limitou suas publicações para evitar spam.
   
   Próximas ações:
   1. Bot pausará por 12-24 horas automaticamente
   2. Voltaremos ao normal em breve

✅ Você faz:

   1. Nada! Bot pausa automático
   2. Aguarde 12-24 horas
   3. Execute bot novamente
   4. Sistema continuará onde parou

════════════════════════════════════════════════════════════════════════════════

DICAS DE OURO 💎

✅ Melhor momento: Terça a Quinta (menos concorrência)

✅ Melhor hora: Entre 10:00-12:00 e 14:00-16:00

✅ Descrições: Faça uma boa descrição, ajude na validação do Facebook

✅ Imagens: Pelo menos 4 fotos boas do imóvel

✅ Preço: Pesquise preços similares, seja competitivo

✅ Paciência: Primeiro imóvel pode demorar mais (Facebook avalia)

✅ Diversidade: Não publique mesma casa 2x, varia localização

════════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING

❌ "Erro: Não consegui conectar ao Neon"
→ Verificar CONNECTION STRING em .env ou config.py
→ Testar acesso em https://console.neon.tech/

❌ "Nenhum imóvel selecionado"
→ Clicar na página ANTES do CTRL + CLIQUE
→ Deve aparecer borda laranja no imóvel

❌ "Imóvel inválido"
→ Faltam dados obrigatórios (veja no log)
→ Tentar outro imóvel com mais informações

❌ "Bloqueado por Facebook"
→ Bot pausa automático por 12-24h
→ Aguarde e execute novamente

════════════════════════════════════════════════════════════════════════════════

Parabéns! Você agora tem uma automação robusta funcionando! 🎉

═══════════════════════════════════════════════════════════════════════════════════
