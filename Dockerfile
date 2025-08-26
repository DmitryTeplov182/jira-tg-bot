FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash botuser

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Копируем код приложения
COPY . .

# Меняем владельца файлов на botuser
RUN chown -R botuser:botuser /app

# Переключаемся на пользователя botuser
USER botuser

# Добавляем pip в PATH для пользователя
ENV PATH="/home/botuser/.local/bin:$PATH"

# Запускаем бота
CMD ["python", "./bot.py"]
