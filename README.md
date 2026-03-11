# University Admission Bot

Telegram-бот приёмной комиссии МТУСИ с RAG-поиском по локальной базе знаний.

Бот принимает вопросы абитуриентов, находит релевантные фрагменты в базе документов, ранжирует контекст и генерирует ответ через Ollama.

## Что умеет

- отвечать на вопросы о поступлении через Telegram
- искать контекст в локальной базе знаний
- работать и с FAQ, и с длинными документами
- хранить историю сообщений в PostgreSQL
- использовать Qdrant для векторного поиска
- измерять качество ответов через встроенный benchmark

## Как это устроено

```text
Пользователь в Telegram
        |
        v
+----------------------+
|   Aiogram handlers   |
+----------------------+
        |
        v
+----------------------+
|     ChatService      |
+----------------------+
        |
        +------------------------------+
        |                              |
        v                              v
+----------------------+    +----------------------+
|      Retriever       |    |  MessageRepository   |
+----------------------+    +----------------------+
        |
        v
+----------------------+
|       Qdrant         |
|  FAQ + doc chunks    |
+----------------------+
        |
        v
+----------------------+
|   RerankerService    |
+----------------------+
        |
        v
+----------------------+
|     Ollama LLM       |
+----------------------+
        |
        v
Ответ пользователю
```

## Стек

- Python 3.13
- Aiogram
- PostgreSQL
- Qdrant
- Ollama
- sentence-transformers

## Структура проекта

- [app](./app) - основной код приложения
- [app/bot](./app/bot) - Telegram handlers
- [app/services](./app/services) - чат-сервис, эмбеддинги, reranker, работа с БД
- [app/rag](./app/rag) - загрузка документов, split, vector store, retrieval
- [scripts](./scripts) - служебные скрипты для инициализации и индексации
- [data](./data) - локальная база знаний
- [tests](./tests) - регрессионные тесты, integration smoke tests, quality benchmark
- [compose.yaml](./compose.yaml) - Docker Compose для dev-режима

## Требования

Для запуска нужны:

- Docker + Docker Compose
- Ollama на хостовой машине
- скачанная модель, например `llama3.1:8b`
- Telegram bot token

Важно: Ollama должен быть доступен из Docker-контейнера. На Linux это обычно означает запуск на `0.0.0.0:11434`, а не только на `127.0.0.1`.

Проверка:

```bash
curl http://localhost:11434/api/tags
ollama list
```

## Переменные окружения

Пример файла: [.env.docker.example](./.env.docker.example)

Основные переменные:

- `BOT_TOKEN` - токен Telegram-бота
- `DATABASE_URL` - строка подключения к PostgreSQL
- `OLLAMA_BASE_URL` - адрес Ollama API
- `OLLAMA_MODEL` - имя модели в Ollama
- `QDRANT_URL` - адрес Qdrant
- `QDRANT_COLLECTION` - имя коллекции в Qdrant

Локально проект читает настройки из `.env`.

## Быстрый старт

### 1. Поднять сервисы

```bash
docker compose up --build
```

Это поднимет:

- `bot`
- `postgres`
- `qdrant`

### 2. Проиндексировать базу знаний

```bash
docker compose --profile tools run --rm indexer
```

Индексатор:

- читает файлы из [data](./data)
- извлекает текст
- режет документы на чанки
- создаёт эмбеддинги
- пересоздаёт коллекцию в Qdrant
- загружает все документы заново

Важно: сейчас индексация работает как полная переиндексация, а не incremental update.

### 3. Проверить бота

После индексации можно отправлять вопросы боту в Telegram.

## Разработка через Docker

Проект настроен под Docker-based dev flow.

Исходники монтируются в контейнер, поэтому обычные правки Python-кода не требуют пересборки образа.

Типовой цикл работы:

1. Запуск:

```bash
docker compose up --build
```

2. Индексация:

```bash
docker compose --profile tools run --rm indexer
```

3. Правки кода локально.

4. Перезапуск только бота:

```bash
docker compose restart bot
```

5. Если изменились документы в [data](./data), выполните переиндексацию:

```bash
docker compose --profile tools run --rm indexer
```

Пересборка нужна в основном только если менялись `requirements.txt` или `Dockerfile`.

## Локальный запуск без Docker

Если вы хотите запускать проект из локального Python-окружения:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.init_db
python -m scripts.load_documents
python -m app.main
```

При этом PostgreSQL, Qdrant и Ollama всё равно должны быть доступны.

## Тесты

### Обычные тесты

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Покрыто:

- регрессии в retrieval
- поведение `vector_store`
- integration smoke test для in-memory Qdrant

### Benchmark качества ответов

В проекте есть end-to-end benchmark, который прогоняет контрольные вопросы через реальный `chat_service` и размечает ответы как:

- `ok`
- `partial`
- `wrong`

Базовый набор:

```bash
docker compose exec bot python -m tests.quality_benchmark --suite basic
```

Сложный набор:

```bash
docker compose exec bot python -m tests.quality_benchmark --suite hard
```

Все кейсы:

```bash
docker compose exec bot python -m tests.quality_benchmark --suite all
```

Полезные флаги:

```bash
docker compose exec bot python -m tests.quality_benchmark --suite hard --limit 5
docker compose exec bot python -m tests.quality_benchmark --suite all --json
```

## Полезные команды

Логи бота:

```bash
docker compose logs -f bot
```

Проверка Qdrant:

```bash
curl http://localhost:6333/collections
```

Сброс коллекции:

```bash
python -m scripts.reset_qdrant
```

Быстрая проверка retrieval:

```bash
python -m scripts.test_retrieval
```

## Ограничения

- Лучше всего бот работает на FAQ-подобных вопросах о поступлении.
- На двусмысленных вопросах качество всё ещё зависит от prompt и retrieval.
- Первая загрузка моделей внутри контейнера может быть долгой.
- Сейчас есть warning о несовпадении версий `qdrant-client` и сервера Qdrant. Работе это не мешает, но версии лучше выровнять.
- Ollama в текущей схеме живёт вне Docker.

## Заметки

- Индексация сейчас полная, не инкрементальная.
- В репозитории уже есть инструменты для измеримой проверки качества ответов после изменений prompt или retrieval.
