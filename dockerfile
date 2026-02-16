# Dockerfile
FROM python:3.11-slim

# Установка зависимостей для GUI
RUN apt-get update && apt-get install -y \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    libxfixes3 \
    libxrandr2 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxcursor1 \
    libxi6 \
    libxcomposite1 \
    libxslt1.1 \
    libxtst6 \
    libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY main.py .

# Создание пользователя для запуска GUI
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Команда для запуска
CMD ["python", "main.py"]