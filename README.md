# LMS Project (Django + DRF + Docker)

Учебный проект системы управления обучением (LMS) на стеке: **Python 3.12**, **Django**, **Django REST Framework**, **PostgreSQL**, **Redis**.  
Развёртывание полностью через **Docker Compose** с healthchecks, volumes и разделением секретов через `.env`.

## Технологический стек

- **Backend**: Django 5.x, Django REST Framework
- **Database**: PostgreSQL 16 (в Docker)
- **Cache**: Redis (в Docker)
- **Сборка и запуск**: Docker Compose (version 3.x)
- **Управление зависимостями**: Poetry
- **Язык**: Python 3.12

---

## Быстрый старт

### 1. Клонируй репозиторий
```bash
git clone https://github.com/fess88888/lms-project
cd lms-project
```


### 2. Проверить

1. **Запуск**: `docker compose up -d` — все контейнеры в статусе `healthy`.
2. **Миграции**: `docker compose run --rm web python manage.py migrate` — `No migrations to apply` или успешное применение.
3. **Статика**: `docker compose run --rm web python manage.py collectstatic --noinput` — файлы собраны.
4. **Суперпользователь**: `docker compose exec web python manage.py createsuperuser` — пользователь создан.