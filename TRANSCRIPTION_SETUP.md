# Инструкция по настройке транскрибации

## ✅ Установлено на сервере

1. **faster-whisper>=0.10.0** - библиотека для быстрой транскрибации аудио
2. Сервис CRM успешно перезапущен

## Проверка установки

### На сервере:
```bash
ssh root@147.45.215.199
cd /var/www/crm
source venv/bin/activate
python -c "from faster_whisper import WhisperModel; print('✅ OK')"
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

### Ошибка: Out of Memory
**Решение**: Используется модель `tiny` для экономии памяти. Если проблема сохраняется:
- Уменьшить `num_workers` до 1 (уже сделано)
- Использовать меньшие файлы
- Разбить большие файлы на части

## Зависимости

Все зависимости указаны в `requirements.txt`:
```
faster-whisper>=0.10.0  # Fast Whisper transcription
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
