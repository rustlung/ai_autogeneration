# AI Client Report Generator

Инструмент для автоматического анализа клиентских диалогов и генерации структурированных PDF-отчётов с использованием OpenAI API.

---

## 🚀 Features

- 🤖 AI-анализ диалогов (OpenAI GPT)
- 📄 Генерация PDF через HTML + WeasyPrint
- 🎨 Кастомизируемые шаблоны (Jinja2 + CSS)
- 💾 Кэширование AI-ответов (экономия токенов)
- 📝 Детальное логирование
- 🔄 Retry-логика при ошибках API
- 🛡️ Обработка исключений и корректные exit-коды

---

## 📸 Demo

```markdown
![Report Example](assets/report_example.pdf)
![Report Example](assets/report_example_site.pdf)
🏗 Project Structure
main.py — точка входа

utils/ — обработка AI, генерация PDF, схемы данных

services/ — OpenAI клиент

templates/ — HTML/CSS шаблоны

cache/ — кэш AI-ответов

logs/ — логирование

reports/ — итоговые PDF

⚙️ Installation
bash
Копировать код
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate
pip install -r requirements.txt
Требуются системные зависимости для WeasyPrint (см. официальную документацию).

🔧 Configuration
Создайте .env на основе .env.example:

env
Копировать код
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
CACHE_DIR=cache/ai_outputs
LOG_LEVEL=INFO
▶️ Usage
Интерактивный режим:

bash
Копировать код
python main.py
CLI-режим:

bash
Копировать код
python main.py --input transcript.txt --output report.pdf
Отключить кэш:

bash
Копировать код
python main.py --no-cache
📦 Tech Stack
Python 3.8+

OpenAI SDK

Pydantic

Jinja2

WeasyPrint

python-dotenv

🛠 Practical Use Case
Автоматизация подготовки отчётов после клиентских встреч

Формирование дизайн-брифов

Анализ обратной связи

Интеграция в CI/CD или CRM-процессы

📜 License
MIT