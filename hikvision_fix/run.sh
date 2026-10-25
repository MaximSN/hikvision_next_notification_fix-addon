#!/usr/bin/with-contenv bashio

# Экспорт параметров из конфигурации Add-on в переменные окружения
export LISTEN_PORT=$(bashio::config 'listen_port')
export TARGET_HOST=$(bashio::config 'target_host')
export TARGET_PORT=$(bashio::config 'target_port')
export HOST_HEADER_VALUE=$(bashio::config 'host_header_value')
export LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.info "Starting Camera Host Proxy..."
bashio::log.info "Listen: ${LISTEN_PORT}, Target: ${TARGET_HOST}:${TARGET_PORT}, Host: ${HOST_HEADER_VALUE}, Log level: ${LOG_LEVEL}"

python3 /camera_proxy.py 2>&1 | while read -r line; do bashio::log.info "$line"; done