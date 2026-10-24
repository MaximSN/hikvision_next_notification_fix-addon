#!/usr/bin/with-contenv bashio

# Экспорт параметров из конфигурации Add-on в переменные окружения
export LISTEN_PORT=$(bashio::config 'listen_port')
export TARGET_HOST=$(bashio::config 'target_host')
export TARGET_PORT=$(bashio::config 'target_port')
export HOST_HEADER_VALUE=$(bashio::config 'host_header_value')

bashio::log.info "Starting Camera Host Proxy..."
bashio::log.info "Listen: ${LISTEN_PORT}, Target: ${TARGET_HOST}:${TARGET_PORT}, Host: ${HOST_HEADER_VALUE}"

python3 /camera_proxy.py