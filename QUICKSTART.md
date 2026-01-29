# Быстрый старт

Пошаговая инструкция для запуска проекта за 5 минут.

## 1. Установка системных зависимостей

### Windows

Скачайте и установите GTK3 Runtime:
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

После установки добавьте в PATH:
```
C:\Program Files\GTK3-Runtime Win64\bin
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential python3-dev python3-pip \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### macOS

```bash
brew install cairo pango gdk-pixbuf libffi
```

## 2. Установка Python зависимостей

```bash
# Создайте виртуальное окружение
python -m venv venv

# Активируйте его
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

## 3. Настройка

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env и добавьте ваш OpenAI API ключ
# Windows:
notepad .env
# Linux/macOS:
nano .env
```

В файле `.env` замените строку:
```
OPENAI_API_KEY=
```

На:
```
OPENAI_API_KEY=sk-proj-ваш-реальный-ключ-здесь
```

Получить API ключ можно на: https://platform.openai.com/api-keys

## 4. Первый запуск

```bash
# Запустите с примером транскрипта
python main.py
```

Если всё настроено правильно, вы увидите:

```
[1/3] Чтение транскрипта: fixtures\sample_transcript.txt
✓ Прочитано 3421 символов

[2/3] Анализ диалога с помощью ИИ...
  (Используется кэширование)
✓ Анализ завершён
  Клиент: Дмитрий Петров
  Тема: Автоматизация складского учёта

[3/3] Генерация PDF отчёта...

✓ Отчёт успешно создан: reports\report_20260128_HHMMSS.pdf

============================================================
ГОТОВО!
============================================================
Отчёт: C:\...\reports\report_20260128_HHMMSS.pdf
Размер: 42.3 KB
============================================================
```

## 5. Проверка результата

Откройте созданный PDF файл в папке `reports/` - там будет профессионально оформленный отчёт по диалогу.

## Что дальше?

### Обработать свой транскрипт

```bash
python main.py --input path/to/your/transcript.txt
```

### Отключить кэш

```bash
python main.py --no-cache
```

### Использовать свой шаблон

```bash
python main.py --template templates/custom_template.html
```

### Посмотреть все опции

```bash
python main.py --help
```

## Устранение проблем

### Ошибка: "OPENAI_API_KEY is not set"

Проверьте что:
1. Файл `.env` создан (не `.env.example`)
2. В `.env` указан ваш реальный API ключ
3. Нет лишних пробелов вокруг знака `=`

### Ошибка при установке WeasyPrint

- **Windows**: Убедитесь что GTK3 установлен и добавлен в PATH
- **Linux**: Установите все системные библиотеки из шага 1
- **macOS**: Попробуйте переустановить через brew

### Ошибка: "Rate limit exceeded"

Вы превысили лимит запросов к OpenAI API:
1. Подождите несколько минут
2. Проверьте ваш план на platform.openai.com
3. Используйте `--use-cache` для повторных запросов

### Детальная диагностика

Включите детальное логирование:

```bash
python main.py --log-level DEBUG
```

Проверьте `logs/app.log` для подробной информации об ошибках.

## Дополнительно

Полная документация: [README.md](README.md)
Архитектура проекта: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
История изменений: [docs/CHANGELOG.md](docs/CHANGELOG.md)
