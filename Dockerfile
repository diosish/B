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
COPY tests/ tests/ 2>/dev/null || echo "No tests directory found"

# Переключение обратно на appuser
USER appuser

# Команда для запуска тестов
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=app"]

# ==============================================
# СТАДИЯ 4: PRODUCTION
# ==============================================
FROM base as production

# Копирование только необходимых файлов для production
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY run_bot.py .
COPY telegram_bot.py .
COPY requirements.txt .

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