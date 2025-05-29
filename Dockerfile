# ==============================================
# МНОГОСТУПЕНЧАТАЯ СБОРКА DOCKER ОБРАЗА
# ==============================================

# ==============================================
# СТАДИЯ 1: БАЗОВЫЙ ОБРАЗ С ЗАВИСИМОСТЯМИ
# ==============================================
FROM python:3.11-slim as base

# Метаданные
LABEL maintainer="volunteer-system@example.com"
LABEL version="1.0.0"
LABEL description="Volunteer Management System"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создание пользователя для безопасности (не root)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Создание рабочей директории
WORKDIR /app

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================
# СТАДИЯ 2: РАЗРАБОТКА
# ==============================================
FROM base as development

# Установка дополнительных инструментов для разработки
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    black \
    flake8 \
    mypy

# Копирование исходного кода
COPY . .

# Изменение владельца файлов
RUN chown -R appuser:appuser /app

# Переключение на пользователя
USER appuser

# Экспозиция порта
EXPOSE 8000

# Команда запуска для разработки
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==============================================
# СТАДИЯ 3: ТЕСТИРОВАНИЕ
# ==============================================
FROM development as testing

# Возвращаемся к root для установки тестовых зависимостей
USER root

# Установка дополнительных тестовых инструментов
RUN pip install --no-cache-dir \
    coverage \
    pytest-cov \
    httpx

# Копирование тестов
COPY tests/ tests/

# Переключение обратно на appuser
USER appuser

# Команда для запуска тестов
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=app"]

# ==============================================
# СТАДИЯ 4: PRODUCTION
# ==============================================
FROM base as production

# Установка только production зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Копирование только необходимых файлов для production
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY run_bot.py .

# Создание директорий для логов и загрузок
RUN mkdir -p /app/logs /app/uploads && \
    chown -R appuser:appuser /app

# Переключение на пользователя
USER appuser

# Экспозиция порта
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска для production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ==============================================
# СТАДИЯ 5: NGINX (опционально)
# ==============================================
FROM nginx:alpine as nginx

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Экспозиция портов
EXPOSE 80 443

# ==============================================
# СТАДИЯ 6: БЕКАП И МИГРАЦИИ
# ==============================================
FROM base as migrations

# Копирование только миграций
COPY alembic/ alembic/
COPY alembic.ini .
COPY app/models.py app/models.py
COPY app/database.py app/database.py
COPY app/__init__.py app/__init__.py

# Создание скрипта для бекапа
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Creating database backup..."\n\
pg_dump $DATABASE_URL > /backup/backup_$(date +%Y%m%d_%H%M%S).sql\n\
echo "Backup completed!"\n\
' > /usr/local/bin/backup.sh && chmod +x /usr/local/bin/backup.sh

# Создание скрипта для восстановления
RUN echo '#!/bin/bash\n\
set -e\n\
if [ -z "$1" ]; then\n\
  echo "Usage: restore.sh <backup_file>"\n\
  exit 1\n\
fi\n\
echo "Restoring database from $1..."\n\
psql $DATABASE_URL < $1\n\
echo "Restore completed!"\n\
' > /usr/local/bin/restore.sh && chmod +x /usr/local/bin/restore.sh

USER appuser

# Команда для запуска миграций
CMD ["alembic", "upgrade", "head"]