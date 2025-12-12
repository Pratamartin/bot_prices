# bot_prices

Breve README para execução e notas rápidas do projeto `bot_prices` (PriceBot).

Pré-requisitos
- Docker e Docker Compose instalados
- Variáveis de ambiente configuradas (ex.: `TELEGRAM_BOT_TOKEN`, `PRICEBOT_GLOBAL_CHAT_ID`)

Como rodar (modo com Docker Compose)

1. Subir containers (build + run):

```bash
docker-compose up --build
```

2. Criar migrations e aplicar (se necessário):

```bash
# dentro do container web
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

3. Criar um superuser para acessar o Django Admin:

```bash
docker-compose exec web python manage.py createsuperuser
```

4. Configurar webhook (opcional, para desenvolvimento com ngrok):

```bash
# exemplo de comando (substitua pelo token e URL corretos)
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" -d "url=https://<your-ngrok>.ngrok.io/telegram/webhook/"
```

Notas importantes
- O app principal do bot está em `backend/`.
- Handlers do Telegram ficam em `backend/telegram/services/handlers.py`.
- Logs de buscas são gravados no modelo `telegram.SearchLog` e podem ser visualizados pelo Admin (registre o model em `telegram/admin.py`).
- Para testes rápidos do handler, você pode simular um Update chamando `handle_update(update_dict)` em um shell Python.

Variáveis de ambiente úteis
- `TELEGRAM_BOT_TOKEN` — token do bot Telegram
- `TELEGRAM_BOT_ID` — id numérico do bot (usado para detectar quando o bot é adicionado a grupos). Default hardcoded no código.
- `PRICEBOT_GLOBAL_CHAT_ID` — id do chat para broadcast anônimo de buscas

Ajuda / Desenvolvimento
- Código principal do agregador de preços: `prices/services/price_agregator.py`.
- Fontes de preço: `prices/price_sources/`.
- Se quiser que eu rode as migrations e crie um superuser aqui, me autorize a executar comandos no container.

Licença
- Projeto sem licença especificada.
