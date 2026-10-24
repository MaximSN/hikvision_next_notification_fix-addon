Тестировалась интеграция [Hikvision Local](https://github.com/brave0d/hikvision_local)  с камерой DS-2CD2412F-IW (версия прошивки V5.4.5), и была выявлена проблема: сенсоры событий не реагировали на события тревоги.

1. Почему решили сделать аддон
Короткое описание проблемы с камерой DS-2CD2412F-IW (версия прошивки V5.4.5):

При отправке уведомлений о событиях (например, пересечении линии) прошивка камеры Hikvision формирует некорректный сетевой пакет: она отправляет запрос по протоколу HTTP/1.1, но полностью игнорирует обязательный заголовок Host.

Пример из tcpdump:
POST /api/hikvision_local HTTP/1.1
Content-Type: application/xml; charset="UTF-8"
Content-Length: 825

<?xml version="1.0" encoding="UTF-8"?>
<EventNotificationAlert version="1.0" xmlns="urn:psialliance-org">
  <ipAddress><IP_камеры></ipAddress>
  <protocolType>HTTP</protocolType>
  <macAddress><MAC_камеры></macAddress>
  <channelID>1</channelID>
  <dateTime>2026-10-24T16:31:13+03:00</dateTime>
  <activePostCount>19</activePostCount>
  <eventType>linedetection</eventType>
  <eventState>active</eventState>
  <eventDescription>linedetection alarm</eventDescription>
  ...
</EventNotificationAlert>

Почему это приводит к ошибке:

Нарушение стандартов RFC: Согласно спецификации HTTP/1.1, заголовок Host является строго обязательным. Без него запрос считается повреждённым.
Отказ со стороны Home Assistant: Встроенный веб-сервер Home Assistant (aiohttp) при прямой отправке запроса от камеры на порт 8123 видит это нарушение протокола, расценивает пакет как некорректный и сразу сбрасывает соединение, выдавая ошибку:
2026-10-24 15:14:25.893 ERROR (MainThread) [aiohttp.server] Error handling request from <IP_камеры>
Traceback (most recent call last):
  File "/usr/local/lib/python3.14/site-packages/aiohttp/web_protocol.py", line 446, in data_received
    messages, upgraded, tail = self._parser.feed_data(data)
                               ~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "aiohttp/_http_parser.pyx", line 723, in aiohttp._http_parser.HttpParser.feed_data
    raise ex
  File "aiohttp/_http_parser.pyx", line 938, in aiohttp._http_parser.cb_on_headers_complete
    pyparser._on_headers_complete()
  File "aiohttp/_http_parser.pyx", line 516, in aiohttp._http_parser.HttpParser._on_headers_complete
    raise BadHttpMessage("Missing 'Host' header in request.")
aiohttp.http_exceptions.BadHttpMessage: 400, message:
  Missing 'Host' header in request.

  2. Описание аддона
Camera Host Proxy — локальный аддон Home Assistant, который:
Слушает заданный порт (по умолчанию 8234) и принимает HTTP-запросы от камеры.
Добавляет заголовок Host с настраиваемым значением (по умолчанию <IP_хоста_HA>).
Пересылает запрос на указанный хост и порт (по умолчанию <IP_хоста_HA>:8123 — Home Assistant).
Возвращает ответ камеры без изменений.
Пишет логи с датой и временем в интерфейс аддона.
Настраиваемые параметры (через вкладку «Конфигурация» аддона):
listen_port — порт прослушивания.
target_host — целевой хост (Home Assistant).
target_port — целевой порт (8123).
host_header_value — значение добавляемого заголовка Host.
Результат: запросы камеры успешно проходят через аддон → Home Assistant (<IP_хоста_HA>:8123).
3. Шаги по созданию локального аддона
3.1. Структура файлов — создайте каталог /addons/hikvision_fix/ со следующими файлами:
   hikvision_fix/
├── config.yaml
├── Dockerfile
├── camera_proxy.py
└── run.sh

3.2. Кодировка и формат файлов — все файлы должны быть сохранены в кодировке UTF-8 с окончаниями строк LF (Unix/Linux).

3.3. Содержимое файлов:
config.yaml — метаданные аддона (имя, версия, архитектуры) и схема параметров, отображаемых в графическом интерфейсе. Раздел options задаёт значения по умолчанию, раздел schema — типы (port, str). Раздел ports пробрасывает порт прослушивания на хост-систему, чтобы камера могла подключиться снаружи контейнера.
Dockerfile — сборка образа на базе ghcr.io/home-assistant/amd64-base:latest, установка python3, копирование скриптов.
camera_proxy.py — сам прокси на Python (только стандартная библиотека). Читает параметры из переменных окружения (LISTEN_PORT, TARGET_HOST, TARGET_PORT, HOST_HEADER_VALUE), принимает HTTP-запросы, добавляет заголовок Host и пересылает на целевой хост.
run.sh — скрипт запуска. Через bashio::config читает параметры из конфигурации аддона и экспортирует их в переменные окружения, затем запускает python3 /camera_proxy.py. Вывод скрипта передаётся в bashio::log.info, чтобы строки отображались в интерфейсе аддона.
3.4. Установка и запуск:
Поместите файлы в /addons/hikvision_fix/.
В Home Assistant перейдите в Настройки → Аддоны → Магазин аддонов, нажмите меню из трёх точек → «Проверить обновления», затем обновите страницу (Ctrl + F5).
В разделе «Локальные аддоны» появится Camera Host Proxy. Нажмите «Установить».
После сборки перейдите на вкладку «Конфигурация» и при необходимости измените параметры (listen_port, target_host, target_port, host_header_value).
Нажмите «Запустить».
Настройте камеру на отправку уведомлений на http://<IP_хоста_HA>:8234/api/hikvision_local.
3.5. Если аддон не появляется или сборка падает: проверьте логи Supervisor (Настройки → Система → Логи → Supervisor). Наиболее частые причины — ошибки в config.yaml (отступы YAML), окончания строк CRLF в run.sh/camera_proxy.py, BOM в начале run.sh, или кеш Docker (решается поднятием version в config.yaml и повторной переустановкой).
Результат: запросы камеры успешно проходят через аддон → Home Assistant (<IP_хоста_HA>:8123)
