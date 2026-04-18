# WavesToDream Backend

REST API для AI-тренера по плаванию. FastAPI + PostgreSQL + Redis.

## Стек

| Компонент | Версия |
|---|---|
| Python | 3.10 |
| FastAPI | ≥ 0.115 |
| SQLAlchemy async | 2.0 |
| PostgreSQL | 15 |
| Redis | 7 |

## Быстрый старт

### 1. Скопируй `.env`

```bash
cp .env.example .env
```

### 2. Запусти Docker

```bash
docker compose up --build -d
```

Сервисы:
- `http://localhost:8000` — FastAPI
- `localhost:5432` — PostgreSQL
- `localhost:6379` — Redis

### 3. Примени миграции

```bash
docker compose exec app alembic upgrade head
```

### 4. Загрузи seed-тренировки

```bash
docker compose exec app python seeds/workouts_seed.py
```

### 5. Swagger UI

[http://localhost:8000/docs](http://localhost:8000/docs)

---

## Переменные окружения

| Переменная | Описание |
|---|---|
| `DATABASE_URL` | asyncpg строка подключения |
| `REDIS_URL` | URL Redis |
| `SECRET_KEY` | Ключ для JWT (мин. 32 символа) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access token (по умолчанию 30) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh token (по умолчанию 7) |
| `AI_API_URL` | URL OpenAI-совместимого провайдера |
| `AI_API_KEY` | API ключ |
| `AI_MODEL` | Название модели |
| `CORS_ORIGINS` | Разрешённые origins через запятую |
| `ADMIN_EMAIL` | Email первого админа |
| `ADMIN_PASSWORD` | Пароль первого админа |

---

## API Эндпоинты

### Auth
| Метод | URL | Описание |
|---|---|---|
| POST | `/api/v1/auth/register` | Регистрация |
| POST | `/api/v1/auth/login` | Вход |
| POST | `/api/v1/auth/refresh` | Обновление токена |
| POST | `/api/v1/auth/logout` | Выход |

### Users
| Метод | URL |
|---|---|
| GET | `/api/v1/users/me` |
| PATCH | `/api/v1/users/me` |

### Swim Profile
| Метод | URL |
|---|---|
| GET | `/api/v1/swim-profile/me` |
| POST | `/api/v1/swim-profile/` |
| PATCH | `/api/v1/swim-profile/me` |

### Chat (требует подписки)
| Метод | URL |
|---|---|
| POST | `/api/v1/chat/message` |
| GET | `/api/v1/chat/history` |

### History
| Метод | URL |
|---|---|
| GET | `/api/v1/history/` |
| GET | `/api/v1/history/{id}` |
| POST | `/api/v1/history/save` |

### Subscriptions & Payments
| Метод | URL |
|---|---|
| GET | `/api/v1/subscriptions/me` |
| POST | `/api/v1/payments/` |
| GET | `/api/v1/payments/me` |

### Admin (role=admin)
| Метод | URL |
|---|---|
| GET | `/api/v1/admin/payments/` |
| PATCH | `/api/v1/admin/payments/{id}/approve` |
| PATCH | `/api/v1/admin/payments/{id}/decline` |
| GET | `/api/v1/admin/users/` |
| GET | `/api/v1/admin/stats/` |

---

## Логика доступа к чату

| Условие | Доступ |
|---|---|
| `single_workout_available = true` | 1 запрос, флаг сбрасывается |
| Подписка `base` | 3 запроса в день |
| Подписка `pro` | Безлимит |
| Нет подписки | `403 Нужна подписка` |