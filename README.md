# LMS Project (Django + DRF + Docker)

Учебный проект системы управления обучением (LMS) на стеке: **Python 3.12**, **Django**, **Django REST Framework**, **PostgreSQL**, **Redis**.

Развёртывание полностью через **Docker Compose** с healthchecks, volumes и разделением секретов через `.env`. Инфраструктура автоматизирована: CI/CD через GitHub Actions (тесты, линтер, сборка образа, деплой по SSH).

## Технологический стек

- **Backend**: Python 3.12, Django 5.x, Django REST Framework
- **Аутентификация**: SimpleJWT (access/refresh токены)
- **Database**: PostgreSQL 16 (в Docker)
- **Брокер и кэш**: Redis (в Docker)
- **Асинхронные задачи**: Celery + Celery Beat
- **Платежи**: Stripe (Checkout Session)
- **Документация API**: drf-spectacular (Swagger / ReDoc)
- **Управление зависимостями**: Poetry
- **Тестирование**: pytest + coverage (15 тестов, покрытие фиксируется в CI)
- **Линтинг и стиль**: flake8, isort

---

## Возможности проекта

- **Курсы и уроки**: CRUD для курсов и уроков, валидация ссылок на YouTube-видео.
- **Права доступа**: владелец управляет своим контентом; модераторы (группа `moderators`) имеют доступ на чтение ко всем курсам и урокам; обычные пользователи видят только свои уроки.
- **Подписки**: toggle-эндпоинт для подписки/отписки на курс (`POST /api/courses/<id>/subscribe/`), поле `is_subscribed` в списке курсов.
- **Платежи**: создание Stripe Checkout Session, отслеживание статуса платежа, страницы success/cancel.
- **Асинхронность**: Celery-задачи (например, уведомление об обновлении курса) и периодические задачи через Celery Beat.
- **Пагинация**: стандартная пагинация DRF для списков курсов и уроков.
- **Кастомные permissions**: `LessonOwnerOrModeratorReadOnly`, `ModeratorReadOnlyForCreationAndDeletion`.

---

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/fess88888/lms-project
cd lms-project
```

### 2. Настройте переменные окружения

Скопируйте шаблон и заполните значения:

```bash
cp .env.example .env
```

Основные переменные `.env`:

| Переменная | Пример | Назначение |
|---|---|---|
| `DJANGO_SECRET_KEY` | `<секретная строка>` | Секретный ключ Django |
| `DEBUG` | `True` / `False` | Режим отладки |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Разрешённые хосты |
| `DB_NAME` | `lms_db` | Имя базы PostgreSQL |
| `DB_USER` | `lms_user` | Пользователь БД |
| `DB_PASSWORD` | `<пароль>` | Пароль БД |
| `DB_HOST` | `db` | Хост БД (имя сервиса compose) |
| `DB_PORT` | `5432` | Порт БД |
| `REDIS_HOST` | `redis` | Хост Redis (имя сервиса compose) |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Брокер Celery |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Хранилище результатов задач |
| `STRIPE_SECRET_KEY` | `sk_test_...` | Секретный ключ Stripe |
| `STRIPE_PUBLISHABLE_KEY` | `pk_test_...` | Публичный ключ Stripe |

> В `.env` для локального запуска `DB_HOST` и `REDIS_HOST` — имена docker-сервисов (`db`, `redis`). В CI используются `localhost`, а Celery переводится в eager-режим.

### 3. Запустите проект

Поднимите все контейнеры (web, db, redis, worker, beat) в фоновом режиме:

```bash
docker compose up -d
```

Проверьте, что все сервисы в статусе `healthy`:

```bash
docker compose ps
```

### 4. Миграции, статика и суперпользователь

Примените миграции:

```bash
docker compose run --rm web python manage.py migrate
```

Соберите статику:

```bash
docker compose run --rm web python manage.py collectstatic --noinput
```

Создайте суперпользователя для доступа в админку:

```bash
docker compose exec web python manage.py createsuperuser
```

После этого админка доступна на `http://localhost:8000/admin/`, а Swagger-документация — на `/api/docs/` (или `/api/schema/swagger-ui/`, в зависимости от конфигурации).

## Тестирование

### Локально (в контейнере)

При запуске тестов задачи Celery выполняются синхронно, без обращения к брокеру (Redis) — это делает результат тестов предсказуемым и независимым от инфраструктуры.

```powershell
docker compose exec -e CELERY_TASK_ALWAYS_EAGER=true web python manage.py test courses -v 2
```

### Через pytest (с покрытием)

```bash
poetry run pytest --cov --cov-report=term
```

### Что проверяют тесты

- Создание, чтение, изменение и удаление уроков владельцем;
- Запрет создания/удаления уроков чужих курсов (403);
- Валидация ссылки на YouTube (400 при некорректной ссылке);
- Видимость уроков: аноним — пустой список, владелец — свои, модератор — все;
- Toggle-подписка: создание (201), удаление (200), аноним (401);
- Отображение признака подписки в списке курсов.

### Ключевая переменная `CELERY_TASK_ALWAYS_EAGER`

- `CELERY_TASK_ALWAYS_EAGER=true` — задачи выполняются сразу в текущем процессе, как обычные функции;
- `task_eager_propagates=true` — исключения из задач пробрасываются в вызывающий код;
- `task_ignore_result=true` — Celery не обращается к Redis за результатами задач.

Настройки применяются автоматически в `config/celery.py` при наличии переменной окружения. **В продакшне переменная не используется** — там Celery работает асинхронно через Redis.

---

## Линтинг и порядок импортов

В проекте настроены `flake8` и `isort`. Если CI падает с ошибкой `Imports are incorrectly sorted`, выполните локально:

```powershell
poetry run isort .
```

Проверка без применения изменений:

```powershell
poetry run isort --diff .
poetry run flake8 .
```

---

## CI/CD: GitHub Actions

Пайплайн запускается:

- при каждом `push` в ветки `main` и `feat/prod-deploy`;
- при открытии `pull_request` в `main`.

### Джобы пайплайна

1. **test** — поднимает PostgreSQL как сервис, устанавливает зависимости через Poetry, запускает pytest с покрытием (`CELERY_TASK_ALWAYS_EAGER=true` отключает зависимость тестов от Redis).
2. **lint** — проверка `flake8` и порядка импортов `isort --check-only`.
3. **build** — сборка Docker-образа с тегом по SHA коммита.
4. **deploy** — срабатывает только при `push` в `main` (после успешных test, lint и build).

### Деплой на сервер

Job `deploy` заходит на сервер по SSH (через `appleboy/ssh-action`) и выполняет:

```bash
cd ~/lms-project
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
```

### Необходимые секреты

В GitHub: **Settings → Secrets and variables → Actions**:

- `SSH_HOST` — IP или домен сервера;
- `SSH_PRIVATE_KEY` — приватный SSH-ключ пользователя `deploy`.

Сервер должен иметь установленные Docker и Docker Compose, а в `~/lms-project` — клонированный репозиторий.

---

## Основные эндпоинты API

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/courses/` | Список курсов (с `is_subscribed`) |
| `POST` | `/api/courses/` | Создание курса |
| `GET/PUT/PATCH/DELETE` | `/api/courses/<id>/` | Детали/изменение/удаление курса |
| `GET` | `/api/lessons/` | Список уроков (свой — пользователю, все — модератору) |
| `POST` | `/api/lessons/` | Создание урока (только владелец курса) |
| `PATCH/DELETE` | `/api/lessons/<id>/` | Изменение/удаление урока |
| `POST` | `/api/courses/<id>/subscribe/` | Toggle подписки: 201 — подписка создана, 200 — удалена |
| `POST` | `/api/payments/` | Создание Stripe Checkout Session |
| `GET` | `/api/payments/<session_id>/status/` | Статус платежа |
| `POST` | `/api/token/`, `/api/token/refresh/` | Получение и обновление JWT |

---
