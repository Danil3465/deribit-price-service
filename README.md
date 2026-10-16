# Deribit Price Service

Сервис, который каждую минуту забирает индексные цены BTC/USD и ETH/USD с биржи Deribit, сохраняет их в PostgreSQL и отдаёт через REST API на FastAPI.

## Стек

* Python 3.12
* FastAPI + Pydantic v2
* SQLAlchemy 2.0 (async) + asyncpg
* PostgreSQL 16
* Celery + Redis (broker и backend)
* aiohttp (клиент Deribit)
* Alembic (миграции)
* Docker + docker-compose
* pytest + pytest-asyncio + httpx (тесты)

## Архитектура

Проект разбит на слои. Вот как выглядит структура:

* app/api/ — роуты FastAPI и зависимости (DI)
* app/clients/ — клиент Deribit на aiohttp
* app/models/ — SQLAlchemy-модели
* app/repositories/ — доступ к данным
* app/schemas/ — Pydantic-схемы ответов
* app/services/ — бизнес-логика
* app/tasks/ — Celery: приложение и задача
* app/config.py — настройки через pydantic-settings
* app/database.py — engine, session factory, Base
* app/main.py — точка входа

Поток данных:

Celery Beat -> Celery Worker -> DeribitClient -> PostgreSQL
HTTP-клиент -> FastAPI -> Service -> Repository -> PostgreSQL

API ничего не знает о SQLAlchemy. Сервис не знает о FastAPI. Репозиторий не знает о HTTP. Каждый слой отвечает только за своё.

## Быстрый старт

1. Скопируй .env.example в .env:

cp .env.example .env

2. Подними контейнеры:

docker compose up --build

Поднимутся пять сервисов: db, redis, app, celery\_worker, celery\_beat.

3. Примени миграции (в отдельном терминале):

docker compose exec app alembic upgrade head

4. Проверь, что всё работает:
* http://localhost:8000/health
* http://localhost:8000/docs

Через минуту после старта Celery Beat запустит первую задачу — цены появятся в БД.

## API

Все методы — GET. Параметр ticker обязателен.

### Получить все сохранённые данные по валюте

GET /api/v1/prices?ticker=btc\_usd

Ответ:

\[
{"ticker": "btc\_usd", "price": "80284.22000000", "timestamp": 1792071136}
]

### Получить последнюю цену

GET /api/v1/prices/latest?ticker=btc\_usd

Если данных нет — 404.

### Получить цены за период

GET /api/v1/prices/by-date?ticker=btc\_usd\&from\_ts=1792000000\&to\_ts=1792100000

from\_ts и to\_ts — UNIX timestamp в секундах, включительно.

## Тесты

docker compose exec app pytest -v

9 тестов: 4 на репозиторий, 5 на API. Используют SQLite in-memory.

## Переменные окружения

|Переменная|Описание|Пример|
|-|-|-|
|DATABASE\_URL|Строка подключения к PostgreSQL|postgresql+asyncpg://postgres:postgres@db:5432/deribit|
|REDIS\_URL|Строка подключения к Redis|redis://redis:6379/0|
|DERIBIT\_BASE\_URL|Базовый URL Deribit API|https://www.deribit.com/api/v2|
|FETCH\_INTERVAL\_SECONDS|Интервал опроса Deribit|60|

Настоящие значения хранятся в .env, который добавлен в .gitignore.

## Design decisions

### Почему Decimal, а не float для цены

float в Python — двоичное число с плавающей точкой. Оно не может точно представить десятичные дроби: 0.1 + 0.2 даёт 0.30000000000000004. Для биржевых цен это недопустимо. Decimal хранит числа точно. В модели — Numeric(18, 8): 18 цифр всего, 8 после запятой. Этого хватает для любой криптовалютной пары.

### Почему timestamp — BigInteger, а не DateTime

Задание прямо требует UNIX timestamp. Это целое число секунд с 1970 года. Хранить его как BigInteger быстрее, чем конвертировать в DateTime, и не создаёт проблем с часовыми поясами. BigInteger, а не Integer, потому что текущий UNIX timestamp (1.7+ млрд) не влезает в 32-битный Integer со знаком.

### Почему составной индекс (ticker, timestamp)

Все три GET-метода фильтруют по ticker. Два из трёх — дополнительно по timestamp. Без индекса каждый запрос делает full scan. С составным индексом база сразу прыгает в нужный диапазон. Для миллиона строк это разница в разы.

### Почему aiohttp, а не httpx или requests

requests синхронный — блокирует поток. В асинхронном приложении это неприемлемо. httpx и aiohttp оба асинхронные. aiohttp был указан в необязательных требованиях задания, поэтому выбрали его. Он более классический для клиентов к внешним API.

### Почему asyncio.run() внутри Celery-задачи

Celery работает синхронно. Наш клиент Deribit — асинхронный. Прямого способа подружить их нет. asyncio.run() создаёт новый event loop внутри задачи, выполняет корутину и закрывает loop. Это стандартный приём. Альтернатива — celery\[asyncio] или писать клиент синхронно. Оба варианта сложнее и не дают выгоды на таком объёме задач.

### Почему Query(...) для ticker

FastAPI автоматически валидирует обязательные query-параметры. Если ticker не передан — вернётся 422 Unprocessable Entity с понятным описанием. Не нужно писать проверку вручную в каждом роуте.

### Почему версионирование /api/v1/

Если завтра изменится формат ответа, старые клиенты продолжат работать на /api/v1/, новые уйдут на /api/v2/. Без версионирования любое изменение ломает всех потребителей.

### Почему SQLite для тестов

Тесты должны быть быстрыми и изолированными. SQLite in-memory создаётся за миллисекунды, не требует контейнера, не оставляет данных. Для unit-тестов этого достаточно.

Минус: SQLite и PostgreSQL не полностью совместимы. В частности, BigInteger с autoincrement=True не работает в SQLite — автоинкремент поддерживается только для Integer. Решение — BigInteger().with\_variant(Integer, "sqlite"): SQLAlchemy использует BigInteger везде, кроме SQLite.

В реальном проекте для интеграционных тестов я бы поднял тестовый PostgreSQL в CI. Для тестового задания SQLite — осознанный компромисс.

### Почему пять контейнеров, а не два

В задании «два контейнера» — необязательное требование, означающее «контейнеризуй приложение и базу». С Celery и Redis меньше не получится:

* app — FastAPI
* db — PostgreSQL
* redis — брокер Celery
* celery\_worker — исполнитель задач
* celery\_beat — планировщик

Это минимальный рабочий набор.

### Почему репозиторий, а не запросы в роутах

Если завтра мы решим перейти с PostgreSQL на другую базу, изменения затронут только репозиторий. Роуты, сервисы и схемы останутся прежними. Это и есть смысл слоистой архитектуры: каждый слой меняется независимо.

### Почему from\_ts / to\_ts, а не from / to

from — зарезервированное слово в Python. Нельзя использовать его как имя параметра. Варианты: from\_, date\_from, from\_ts. Выбрали from\_ts — короче и явно указывает, что это timestamp.

## Что можно улучшить

* Retry-логика для Deribit. Если биржа недоступна, задача сейчас просто логирует ошибку. Стоит добавить exponential backoff.
* Пагинация для get\_all. Если данных много, ответ будет огромным. Стоит добавить limit / offset.
* Мониторинг Celery. Flower даёт веб-интерфейс для отслеживания задач.
* Structlog вместо стандартного logging. Структурированные логи удобнее парсить и анализировать.
* Тестовый PostgreSQL в CI. Для интеграционных тестов, где важна совместимость с продовой БД.
* Health-check для Celery. Сейчас /health проверяет только FastAPI. Стоит добавить проверку, что воркер жив.

