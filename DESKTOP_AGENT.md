# Agente desktop de publicação

O backend e o dashboard podem ficar hospedados. O agente roda no computador que
precisa mostrar o Chromium; o navegador, o perfil do Facebook e os cookies ficam
nesse computador. A publicação continua exigindo revisão e confirmação humana.

## Configurar o servidor

1. Gere um segredo aleatório:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

2. Configure o resultado como `DESKTOP_AGENT_TOKEN` nas variáveis de ambiente do
   serviço de API. Use HTTPS no endereço público da API.
3. Faça deploy/reinicie o serviço após definir a variável.

O token concede acesso apenas aos endpoints de trabalho do agente, mas deve ser
tratado como segredo. Use um token diferente por instância hospedada e não o
coloque no frontend, no Git ou em imagens públicas.

## Instalar o agente no computador do operador

No Windows, instale Python 3.12+ e Git. Clone o repositório, abra PowerShell na
pasta do projeto e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Crie um `.env` local (não publique esse arquivo) com:

```dotenv
DESKTOP_AGENT_API_URL=https://sua-api.example.com
DESKTOP_AGENT_TOKEN=cole-aqui-o-segredo-configurado-no-servidor
BROWSER_HEADLESS=false
```

Inicie o worker com o computador conectado à internet:

```powershell
.\.venv\Scripts\python.exe -m backend.desktop_agent
```

Deixe essa janela aberta. Entre no dashboard hospedado, solicite a publicação e
acompanhe o Chromium que será aberto localmente. Na primeira execução, entre no
Facebook nesse Chromium e mantenha o perfil local. Revise o anúncio, conclua a
publicação no Facebook e só então clique em confirmar no dashboard.

## Limites e segurança

- O agente deve ficar rodando enquanto houver tarefas; se estiver desligado, a
  fila mostrará “aguardando agente desktop”.
- Se o agente encerrar durante a preparação, a tarefa sem heartbeat por 2 minutos
  será marcada como erro para permitir uma nova tentativa pelo dashboard.
- O perfil/cookies do Facebook nunca são enviados à API.
- Não compartilhe o token nem a pasta `perfil_playwright`.
- A aplicação atual tem um banco/fila administrativo compartilhado por instância.
  Para atender clientes independentes em uma única instalação SaaS, ainda é
  necessário implementar usuários, tenants e isolamento dos registros por
  cliente. Até lá, use uma instância de servidor e um token próprios por
  organização; não entregue acesso ao dashboard compartilhado a clientes não
  confiáveis.
- O agente controla o fluxo do navegador e deixa o anúncio para conferência
  humana; não contorna CAPTCHA nem controles de segurança da plataforma.
