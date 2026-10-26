# Instalação por cliente: API, SQLite e agente desktop

Cada organização deve ter sua própria instância da API, seu próprio arquivo
SQLite em armazenamento persistente, seu próprio dashboard e seu próprio token
de agente. O agente roda no computador do operador que precisa mostrar o
Chromium; o navegador, o perfil do Facebook e os cookies ficam nesse computador.
A publicação continua exigindo revisão e confirmação humana.

Neste guia, a hospedagem da API usa Render e o dashboard usa Vercel. Os dados
ficam isolados por organização porque cada uma usa serviços e armazenamento
separados — não crie um usuário/tenant adicional dentro de uma mesma instância.

## 1. Criar a API exclusiva da organização no Render

Repita estes passos para cada organização:

1. No Render, crie um **Web Service** a partir deste repositório. Dê a ele um
   nome exclusivo, por exemplo `as-bot-imobiliaria-cliente-a`.
2. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Na página do serviço, adicione um **Persistent Disk**:
   - **Mount Path:** `/var/data`
   - Escolha o tamanho necessário. O disco persistente exige um plano Render
     compatível; o filesystem padrão é temporário.
4. Em **Environment**, configure variáveis únicas para esta organização:

   ```dotenv
   DATABASE_URL=sqlite:////var/data/onora-imob.db
   ADMIN_USERNAME=admin-cliente-a
   ADMIN_PASSWORD=defina-uma-senha-forte-e-exclusiva
   SECRET_KEY=gere-um-segredo-aleatorio
   DESKTOP_AGENT_TOKEN=gere-outro-segredo-aleatorio
   BROWSER_HEADLESS=true
   ALLOW_ORIGINS=https://dashboard-cliente-a.vercel.app
   ```

   Gere valores aleatórios para `SECRET_KEY` e `DESKTOP_AGENT_TOKEN` com:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   O `DATABASE_URL` deve apontar para dentro do mount `/var/data`. Não use o
   caminho SQLite relativo padrão em produção, pois ele fica no filesystem
   temporário do serviço.
5. Salve as variáveis e aguarde o deploy. Confira
   `https://<url-do-servico>.onrender.com/health`; a resposta deve mostrar
   `"status": "ok"` e `"desktop_agent_configured": true`.

Guarde os segredos fora do Git e não reutilize credenciais ou token de uma
organização em outra. O disco Render só persiste o que estiver dentro de
`/var/data`; faça backup periódico do banco.

Se uma instância já tem anúncios em outro banco, não troque `DATABASE_URL`
esperando que os dados sejam copiados: a aplicação não faz migração automática
entre bancos. Faça e confira um backup/migração antes de mudar a URL.

## 2. Publicar o dashboard exclusivo no Vercel

Para cada organização, crie um projeto Vercel do mesmo repositório:

1. Selecione `frontend` como **Root Directory**.
2. Configure `VITE_API_BASE_URL` com a URL pública da API, sem `/api`, por
   exemplo `https://as-bot-cliente-a.onrender.com`.
3. Faça o deploy e copie a URL final do dashboard.
4. Confira se `ALLOW_ORIGINS` na API corresponde exatamente a essa URL
   (`https://...vercel.app`, sem barra final). Se mudar a URL, atualize a variável
   no Render e faça novo deploy.

O dashboard deve apontar apenas para a API daquele cliente. Não coloque
`DESKTOP_AGENT_TOKEN`, `SECRET_KEY` ou senha administrativa nas variáveis
`VITE_*` do Vercel, pois essas variáveis podem ser incluídas no frontend.

## Instalar o agente no computador do operador

No Windows, instale Python 3.12+ e Git. Clone o repositório, abra PowerShell na
pasta do projeto e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Crie um `.env` local na pasta do projeto (não publique esse arquivo) com:

```dotenv
DESKTOP_AGENT_API_URL=https://as-bot-cliente-a.onrender.com
DESKTOP_AGENT_TOKEN=use-o-token-exclusivo-configurado-no-render
BROWSER_HEADLESS=false
```

Inicie o worker com o computador conectado à internet:

```powershell
.\.venv\Scripts\python.exe -m backend.desktop_agent
```

Deixe essa janela aberta. Entre no dashboard daquele cliente com
`ADMIN_USERNAME`/`ADMIN_PASSWORD`, solicite a publicação e acompanhe o Chromium
que será aberto localmente. Na primeira execução, entre no Facebook nesse
Chromium e mantenha o perfil local. Revise o anúncio, conclua a publicação no
Facebook e só então clique em confirmar no dashboard.

## 4. Repetir para outros clientes

Para cada nova organização, crie uma nova API Render com seu próprio disco e
`DATABASE_URL`, um projeto/dashboard Vercel com `VITE_API_BASE_URL` apontando para
essa API, e instale um agente com o par correspondente de URL e token. Nunca
aponte agentes de organizações diferentes para a mesma API.

## Limites e segurança

- O agente deve ficar rodando enquanto houver tarefas; se estiver desligado, a
  fila mostrará “aguardando agente desktop”.
- Se o agente encerrar durante a preparação, a tarefa sem heartbeat por 2 minutos
  será marcada como erro para permitir uma nova tentativa pelo dashboard.
- O perfil/cookies do Facebook nunca são enviados à API.
- Não compartilhe o token nem a pasta `perfil_playwright`.
- O SQLite fica no disco persistente da instância hospedada; não fica no PC do
  operador. O Chromium visível, o perfil e os cookies ficam no computador do
  agente.
- Mantenha uma única instância da API usando cada arquivo SQLite. Não configure
  várias réplicas ou serviços para abrir o mesmo arquivo de banco.
- Esta solução isola clientes usando uma instância e um disco por organização.
  Ela não implementa isolamento multi-tenant dentro de uma instância
  compartilhada.
- O agente controla o fluxo do navegador e deixa o anúncio para conferência
  humana; não contorna CAPTCHA nem controles de segurança da plataforma.
