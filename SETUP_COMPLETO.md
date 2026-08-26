# 🚀 GUIA PRÁTICO - BOT AS MARKETPLACE v2.0 (100% FUNCIONAL)

## ⚡ INÍCIO RÁPIDO (5 minutos)

### 1. Configure o Banco de Dados Neon

Se ainda não tiver:

```bash
# 1. Acesse: https://console.neon.tech/
# 2. Crie uma conta (gratuita)
# 3. Crie um novo projeto
# 4. Copie a CONNECTION STRING
```

### 2. Configure o Bot

Opção A (Recomendado - Arquivo .env):

```bash
# Crie arquivo .env na raiz do projeto:
DATABASE_URL=postgresql://usuario:senha@ep-xxxxx.neon.tech/neondb
```

Opção B (Config direto em config.py):

```python
NEON_DATABASE_URL = "postgresql://usuario:senha@ep-xxxxx.neon.tech/neondb"
```

### 3. Instale Dependências

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Teste a Conexão

```bash
python test_connection.py
```

Deve retornar: ✅ TESTES CONCLUÍDOS

---

## 🎯 MODO DE USO

### Iniciar o Bot

```bash
python app.py
```

Você verá o menu:

```
🤖 BOT DE PUBLICAÇÃO - FACEBOOK MARKETPLACE
════════════════════════════════════════════

Opções:
  1. 📥 Extrair imóveis da AS Imobiliária
  2. 📤 Publicar próximo imóvel
  3. 📦 Ver fila de publicações
  4. 📊 Ver dashboard
  5. 🚪 Sair
```

---

## 📥 OPÇÃO 1: EXTRAIR IMÓVEIS

### Passo a Passo:

1. **Escolha opção 1**
   - Browser abre automaticamente na AS Imobiliária

2. **Navegue pelos imóveis**
   - Procure os imóveis que quer extrair
   - Acesse cada um deles

3. **Selecione com CTRL + CLIQUE**
   - Segure CTRL e clique em cada imóvel
   - Verá um destaque laranja em cada um selecionado

4. **Pressione ENTER no terminal**
   - Sistema começará a extrair os dados

5. **Escolha quais publicar**
   - Mostra lista dos imóveis extraídos
   - Você escolhe números: `1,3,5` ou ENTER para todos

✅ **Pronto!** Os imóveis foram salvos no banco e adicionados à fila.

---

## 📤 OPÇÃO 2: PUBLICAR IMÓVEL

### Passo a Passo:

1. **Escolha opção 2**
   - Sistema verifica fila
   - Se houver imóvel pronto, mostra dados

2. **Confirme publicação**
   - Digita `S` para sim, `N` para não

3. **Facebook abre automaticamente**
   - Browser acessa Facebook Marketplace
   - Sistema preenche 80% do formulário

4. **Você revisa e publica**
   - Verifica se tudo está correto
   - Adiciona/muda dados se necessário
   - **Você clica em PUBLICAR no Facebook**

5. **Pressione ENTER no terminal**
   - Sistema registra publicação no banco
   - Próxima será agendada para 3h depois

✅ **Publicado!** Imóvel está no Facebook.

---

## 📦 OPÇÃO 3: VER FILA

Mostra:
- Status de cada imóvel (⏳ Aguardando, ✅ Publicado, ❌ Erro, etc)
- Tempo até próxima publicação
- Tentativas de cada um

```
📦 FILA DE PUBLICAÇÕES
════════════════════════════════════════════

Total: 5 imóvel(is)
  ⏳ Aguardando: 2
  ✅ Publicado: 2
  ❌ Erro: 1

🎯 Próximo a publicar:
   Imóvel: Casa 3 quartos em Marília
   Preço: R$ 450.000

📋 Últimos itens na fila:
1. ⏳ Casa bonita - R$500000 | aguardando | em 2h 30m
2. ✅ Casarão histórico - R$800000 | publicado | PRONTO
```

---

## 📊 OPÇÃO 4: DASHBOARD

Menu avançado com:

1. **Ver fila detalhada** - Todos os imóveis
2. **Estatísticas** - Taxa de sucesso, bloqueios, etc
3. **Remover da fila** - Delete imóvel específico
4. **Reprogramar** - Mude data de publicação
5. **Limpar erros** - Remove itens com 5+ falhas
6. **Ver logs** - Histórico completo

---

## ⚠️ BLOQUEIOS DO FACEBOOK

Se Facebook bloquear:

```
╔════════════════════════════════════════════════════════╗
║    CHECKPOINT OU LOGIN REQUERIDO                       ║
╚════════════════════════════════════════════════════════╝

O que fazer:
1. Resolva checkpoint/captcha no Facebook
2. Faça login se necessário
3. Volte para tela de criar anúncio
4. Pressione ENTER aqui

→ Sistema pausará publicações por 12-24h
```

**Soluções:**
- ✅ Resolva o checkpoint manualmente
- ✅ Sistema detecta e pausa automaticamente
- ✅ Dashboard mostra bloqueios ativos
- ✅ Use outra conta do Facebook se bloqueio persistir

---

## 🔧 CONFIGURAÇÕES IMPORTANTES

Em `config.py`:

```python
# Intervalo entre publicações (horas)
HORAS_ENTRE_PUBLICACOES = 3

# Máximo por dia
MAX_ANUNCIOS_POR_DIA = 3

# Horas de pausa se bloqueado
PAUSAR_APOS_BLOQUEIO_HORAS = 12

# Limites de texto
TITULO_MIN = 5
TITULO_MAX = 90
DESCRICAO_MIN = 50
DESCRICAO_MAX = 4500
```

---

## 📊 ESTRUTURA DE DADOS

### Banco PostgreSQL (Neon):

**Tabela: imoveis**
- Todos os imóveis extraídos
- Dados: título, preço, descrição, endereço, imagens

**Tabela: fila_publicacao**
- Agendamento e histórico de publicações
- Status: aguardando, publicado, bloqueado, erro

**Tabela: bloqueios**
- Registro de bloqueios do Facebook
- Tipo e momento detectado

**Tabela: logs**
- Auditoria completa de operações

---

## ✅ CHECKLIST DE FUNCIONAMENTO

Antes de usar:

- [ ] `pip install -r requirements.txt` rodou sem erros
- [ ] `playwright install chromium` instalou navegador
- [ ] `python test_connection.py` retornou ✅
- [ ] DATABASE_URL está configurado em `.env` ou `config.py`
- [ ] Você tem conta no Facebook com permissão Marketplace
- [ ] Chrome está instalado no seu PC

---

## 🐛 TROUBLESHOOTING

### Erro: "postgresql://user:password@..." não funciona

```
→ Copie a CONNECTION STRING corretamente de https://console.neon.tech/
→ Remova "{}" ou placeholders
→ Salve em .env ou config.py
```

### Erro: "Playwright chromium não encontrado"

```bash
playwright install chromium
```

### Imóvel não aparece ao extrair

```
→ Certifique-se que clicou com CTRL + CLIQUE
→ Navegue até a página DO IMÓVEL (não lista)
→ Verifique se a página tem título, preço, descrição
```

### Facebook bloqueia toda publicação

```
→ Use perfil diferente
→ Aguarde 24-48h para desbloqueio
→ Reduza velocidade: aumente HORAS_ENTRE_PUBLICACOES
```

### Banco de dados vazio após restart

```
→ Dados ficam salvos no Neon
→ Não é local - persiste entre execuções
→ Se apagou, execute python app.py e extraia novamente
```

---

## 📈 PRÓXIMOS PASSOS (OPCIONAL)

1. **Automação em Background**: Use `schedule` para rodar publicações automaticamente
2. **Notificações**: Configure email quando publica
3. **Sync de Imagens**: Download automático antes de publicar
4. **WhatsApp**: Receba alertas via WhatsApp

---

## 💡 DICAS DE USO

✅ **Extrator primeiro**: Extraia todos os imóveis desejados antes de publicar
✅ **Fila ativa**: Deixe sistema verificando fila (não fecha)
✅ **Dados completos**: Quanto mais dados, melhor o anúncio
✅ **Imagens boas**: Mínimo 3-4 fotos de cada imóvel
✅ **Descrição detalhada**: Ajuda no Facebook a ranquear melhor

---

## 📞 SUPORTE

Se tiver problemas:

1. Verifique logs em `logs/bot_YYYYMMDD_HHMMSS.log`
2. Rode `test_connection.py` novamente
3. Leia mensagens de erro no terminal
4. Consulte documentação original em `README.md`

---

## ✨ FIM

**O sistema está 100% funcional e pronto para usar!**

Comande:
```bash
python app.py
```

E comece a publicar imóveis no Facebook Marketplace automaticamente! 🎉
