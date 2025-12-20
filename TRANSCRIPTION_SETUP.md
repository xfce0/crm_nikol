# Инструкция по настройке транскрибации

## ✅ Установлено на сервере

1. **faster-whisper>=0.10.0** - библиотека для быстрой транскрибации аудио
2. **ffmpeg** - система для обработки аудио/видео файлов
3. Настроен PATH в systemd службе для доступа к системным утилитам
4. Сервис CRM успешно перезапущен

## Проверка установки

### На сервере:
```bash
ssh root@147.45.215.199
cd /var/www/crm
source venv/bin/activate

# Проверка faster-whisper
python -c "from faster_whisper import WhisperModel; print('✅ faster-whisper OK')"

# Проверка ffmpeg
which ffmpeg && echo '✅ ffmpeg OK'
```

## Как работает транскрибация

Транскрибация выполняется в отдельном subprocess для изоляции памяти:
- **Файл**: `app/services/transcription_service.py`
- **Функция**: `_transcribe_file_subprocess()` (строка 332)
- **Модель**: `tiny` (самая быстрая, для русского языка)
- **Device**: CPU с int8 квантизацией

## Тестирование

1. Загрузите аудио/видео файл через UI транскрипции
2. Проверьте логи на сервере:
   ```bash
   journalctl -u crm.service -f | grep -i "transcrib"
   ```

## Возможные проблемы

### Ошибка: "ModuleNotFoundError: No module named faster_whisper"
**Решение**: Переустановить модуль
```bash
cd /var/www/crm
source venv/bin/activate
pip install --upgrade faster-whisper
systemctl restart crm
```

### Ошибка: "[Errno 2] No such file or directory: 'ffmpeg'"
**Причина**: ffmpeg не установлен или недоступен в PATH службы systemd

**Решение 1**: Установить ffmpeg
```bash
apt-get update && apt-get install -y ffmpeg
```

**Решение 2**: Проверить PATH в службе systemd
Файл `/etc/systemd/system/crm.service` должен содержать:
```ini
Environment="PATH=/var/www/crm/venv/bin:/usr/local/bin:/usr/bin:/bin"
```

После изменений:
```bash
systemctl daemon-reload
systemctl restart crm
```

### Ошибка: Out of Memory
**Решение**: Используется модель `tiny` для экономии памяти. Если проблема сохраняется:
- Уменьшить `num_workers` до 1 (уже сделано)
- Использовать меньшие файлы
- Разбить большие файлы на части

## Зависимости

### Python пакеты (requirements.txt):
```
faster-whisper>=0.10.0  # Fast Whisper transcription
```

### Системные пакеты:
```bash
# Ubuntu/Debian
apt-get install ffmpeg

# Проверка установки
ffmpeg -version
which ffmpeg  # Должен вернуть: /usr/bin/ffmpeg
```

## Логи

Проверить работу транскрибации:
```bash
# На сервере
journalctl -u crm.service -n 100 | grep -i "transcrib\|whisper"
```

## Последнее обновление

- **Дата**: 2025-12-20
- **Статус**: ✅ Установлено и протестировано
- **Версия**: faster-whisper>=0.10.0
