FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные пакеты для сборки зависимостей
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev gcc libffi-dev libssl-dev && \
    apt-get clean

# Обновляем pip
RUN pip install --upgrade pip setuptools wheel uv

# Копируем проект
COPY . .

# Синхронизируем зависимости через UV
RUN pip install -r requirements.txt

# Делаем entrypoint исполняемым
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Стандартная команда запуска контейнера
ENTRYPOINT ["/entrypoint.sh"]
