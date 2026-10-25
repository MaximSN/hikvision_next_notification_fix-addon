FROM ghcr.io/home-assistant/amd64-base:latest

# Установка Python
RUN apk add --no-cache python3

# Копирование скрипта
COPY camera_proxy.py /camera_proxy.py

# Копирование скрипта запуска
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]