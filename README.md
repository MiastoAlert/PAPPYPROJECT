# Pappy Bot

Проект: реферальная система с балансом Pappy, мини-приложением и обменом наград.

## Запуск

1. Установите зависимости:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Настройте переменные окружения в `.env`:
   - `BOT_TOKEN`
   - `ADMIN_IDS` (через запятую)
   - `GROUP_ID`
   - `WEBAPP_URL` (например, `https://your-domain.com/app`)
   - `DB_PATH`

3. Запустите бота:
   ```
   python -m app.main
   ```

4. Запустите веб-сервер мини-приложения:
   ```
   uvicorn app.webapp_server:app --host 0.0.0.0 --port 8000
   ```

## Структура

- `app/handlers` — команды и обработчики
- `app/services` — бизнес-логика
- `app/database` — доступ к SQLite
- `app/webapp` — интерфейс Telegram Web App
