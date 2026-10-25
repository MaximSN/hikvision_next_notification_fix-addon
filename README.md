Тестировалась интеграция [Hikvision Local](https://github.com/brave0d/hikvision_local)  с камерой DS-2CD2412F-IW (версия прошивки V5.4.5), и была выявлена проблема: сенсоры событий не реагировали на события тревоги.

Почему решили сделать аддон
При отправке уведомлений о событиях прошивка камеры Hikvision формирует некорректный по протоколу HTTP/1.1 - отсутствует обязательный заголовок Host.

Пример из tcpdump:
```text
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
```

Согласно спецификации HTTP/1.1, заголовок Host является строго обязательным. Без него запрос считается повреждённым.

При получении такого запроса веб-сервер Home Assistant (aiohttp), расценивает пакет как некорректный и сразу сбрасывает соединение, выдавая ошибку:
```text
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
```
Добавить заголовок настройками камеры или настроить игнорирование в Home Assistant или nginx не получилось. Поэтому был сделан addon.
Addon полностью сгененрирован DeepSeek. Не судите строго :-). Я описал задачу и получил рабочий код.

Описание аддона
old-hikvision-camera-addon — локальный аддон Home Assistant, который:
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

Настройте камеру на отправку уведомлений на http://<IP_хоста_HA>:8234/api/hikvision_local.

