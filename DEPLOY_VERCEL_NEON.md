# Deploy recomendado: Vercel + Neon + VPS/Render

## Arquitetura

- Frontend: Vercel
- Banco: Neon
- Backend + automação: VPS/Render/Railway

## 1. Banco Neon

Use a string de conexão criada no Neon:

```env
DATABASE_URL=postgresql://neondb_owner:npg_lQsfLXA1NI6D@ep-spring-shadow-aysv4jz1-pooler.c-5.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require
```

## 2. Backend em VPS/Render/Railway

Configure as variáveis:

```env
DATABASE_URL=postgresql://neondb_owner:npg_lQsfLXA1NI6D@ep-spring-shadow-aysv4jz1-pooler.c-5.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require
SECRET_KEY=troque-por-uma-chave-forte
ADMIN_USERNAME=admin
ADMIN_PASSWORD=troque-esta-senha
APP_HOST=0.0.0.0
APP_PORT=8000
ALLOW_ORIGINS=https://seu-frontend.vercel.app,https://localhost:5173
```

## 3. Frontend no Vercel

No ambiente do Vercel, adicione:

```env
VITE_API_BASE_URL=https://api.seu-dominio.com
```

Se o backend estiver em outra URL, ajuste para a URL real.

## 4. Regras de operação

- O cliente acessa somente o frontend.
- O backend roda em ambiente separado.
- O browser permanece em sessão controlada no backend.
- Publicação final continua manual, com confirmação do usuário.
- O banco fica no Neon e não no cliente.

## 5. Observação importante

O Vercel não é adequado para rodar Playwright em modo visível/automação ativa. A automação deve ficar em um backend dedicado.
