# 📖 Документация Form Engine

**Проект:** Активация гарантии. Шаблон

Универсальный движок форм для Telegram-ботов. 
Позволяет создавать многошаговые формы через YAML-конфигурацию без правки кода.

## 🚀 Возможности

- ✅ **Универсальный Form Engine** — создание форм через YAML/JSON конфигурацию
- ✅ **Типы полей**: text, phone, email, number, select, date, consent, email_verification
- ✅ **State Management**: сохранение прогресса (memory, FSM, PostgreSQL)
- ✅ **Навигация**: кнопки Назад / Отмена / Начать заново / Пропустить
- ✅ **Review экран**: проверка данных перед отправкой
- ✅ **Валидация**: встроенные валидаторы + regex + кастомные сообщения
- ✅ **Интеграция с Bitrix24**: отправка данных в CRM
- ✅ **PDF сертификаты**: генерация и отправка документов

## 📦 Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

## ⚙️ Конфигурация

### 1. Настройка секретов

Отредактируйте `src/resources/properties/application_properties.yaml`:

```yaml
production:
  bot_token: "YOUR_BOT_TOKEN_HERE"
  
  mail:
    address: "Bot@yourdomain.ru"
    password: "YOUR_EMAIL_PASSWORD_HERE"
    smtp_server: "mail.nic.ru"
    smtp_port: 587
  
  bitrix24:
    webhook: "YOUR_BITRIX24_WEBHOOK_URL_HERE"
  
  postgres:
    host: localhost
    port: 5432
    user: your_db_user
    password: "YOUR_DB_PASSWORD_HERE"
    database: your_db_name
```

### 2. Настройка базы данных

```sql
CREATE DATABASE your_db_name;
CREATE USER your_db_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
```

### 3. Запуск бота

```bash
cd src
python3 main.py
```

## 📝 Создание новой формы

### Шаг 1: Создайте YAML-конфиг

Создайте файл `src/resources/forms/my_form.yml`:

```yaml
form_id: "my_form"
title: "Моя форма"
description: "Описание формы для пользователя"
version: "1.0"

steps:
  # Текстовое поле
  - id: "name"
    type: "text"
    label: "Как вас зовут?"
    required: true
    validation:
      min_len: 2
      max_len: 50
      error_message: "Введите корректное имя"

  # Телефон (автовалидация +7XXXXXXXXXX)
  - id: "phone"
    type: "phone"
    label: "Ваш номер телефона"
    required: true
    hint: "Формат: +7XXXXXXXXXX"

  # Email с верификацией
  - id: "email"
    type: "email"
    label: "Ваш email"
    required: true
  
  - id: "email_code"
    type: "email_verification"
    label: "Введите код из письма"
    required: true

  # Выбор из списка
  - id: "category"
    type: "select"
    label: "Выберите категорию"
    required: true
    options:
      - "Вариант 1"
      - "Вариант 2"
      - "Вариант 3"

  # Согласие
  - id: "consent"
    type: "consent"
    label: "Согласие на обработку данных"
    required: true
    consent_text: "Нажимая кнопку, вы соглашаетесь..."
    agree_button: "Согласен ✅"

  # Дата
  - id: "date"
    type: "date"
    label: "Введите дату"
    required: false
    hint: "Формат: ДД.ММ.ГГГГ"

review:
  enabled: true
  title: "Проверьте данные"

submit:
  button_text: "Отправить"
  success_text: "✅ Готово! Данные отправлены."
  fail_text: "❌ Ошибка отправки."

buttons:
  back: "⬅️ Назад"
  cancel: "❌ Отмена"
  restart: "🔄 Заново"
  skip: "⏭ Пропустить"
```

### Шаг 2: Создайте submit handler

В `src/main/forms/submit_handlers.py` добавьте:

```python
from main.forms.engine import register_submit_handler
from main.forms.schemas import FormSubmitResult

@register_submit_handler("my_form")
async def handle_my_form(data, state, config):
    """
    Обработчик отправки формы.
    
    :param data: Dict с собранными данными {field_id: value}
    :param state: FormState — состояние формы
    :param config: FormConfig — конфигурация формы
    :return: FormSubmitResult
    """
    try:
        # Ваша бизнес-логика
        name = data.get('name')
        phone = data.get('phone')
        
        # Сохранение в БД, отправка в CRM и т.д.
        
        return FormSubmitResult(
            success=True,
            message=f"Спасибо, {name}! Мы свяжемся с вами."
        )
    except Exception as e:
        return FormSubmitResult(
            success=False,
            error=str(e)
        )
```

### Шаг 3: Подключите форму к команде

В `src/main/handler/` создайте новый handler или добавьте в существующий:

```python
from pathlib import Path
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from main.forms import start_form

router = Router()

FORM_PATH = Path(__file__).resolve().parents[2] / "resources" / "forms" / "my_form.yml"

@router.message(Command('my_form'))
async def start_my_form(message: Message, state: FSMContext):
    await start_form(
        event=message,
        state=state,
        form_path=FORM_PATH,
        initial_data={"name": "Предзаполненное имя"}  # опционально
    )
```

Не забудьте добавить router в `main.py`:

```python
from main.handler.my_handler import router as my_router

dispatcher.include_routers(form_router, my_router, ...)
```

## 🔧 Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `USE_FORM_ENGINE` | Использовать Form Engine для гарантии | `1` |
| `FORM_DEBUG` | Включить debug-логирование форм | `0` |

## 📁 Структура проекта

```
src/
├── main/
│   ├── forms/              # 🆕 Form Engine
│   │   ├── __init__.py     # Экспорты
│   │   ├── schemas.py      # Pydantic модели
│   │   ├── validators.py   # Валидаторы полей
│   │   ├── storage.py      # State management
│   │   ├── renderer.py     # Генерация UI
│   │   ├── engine.py       # Логика форм
│   │   ├── handlers.py     # aiogram router
│   │   └── submit_handlers.py  # Обработчики отправки
│   ├── handler/            # Обработчики команд
│   ├── service/            # Бизнес-логика
│   ├── model/              # Модели БД
│   ├── config/             # Конфигурация
│   └── ...
├── resources/
│   ├── forms/              # 🆕 YAML конфиги форм
│   │   └── activation.yml  # Пример формы
│   └── properties/         # Настройки приложения
└── main.py                 # Точка входа
```

## 🧪 Тестирование

### Debug режим

Включите логирование переходов:

```bash
FORM_DEBUG=1 python3 main.py
```

### Ручное тестирование

1. Запустите бота
2. Отправьте `/guarantee` или `/activate_new`
3. Пройдите все шаги формы
4. Проверьте review-экран
5. Отправьте форму

## 📚 API Reference

### FormEngine

```python
from main.forms import FormEngine, load_form

# Загрузка из файла
engine = load_form("path/to/form.yml")

# Запуск формы
await engine.start(message, fsm_context, initial_data=None)

# Обработка ввода
await engine.process_input(message, fsm_context)

# Обработка callback
await engine.process_callback(callback_query, fsm_context)
```

### start_form

```python
from main.forms import start_form

await start_form(
    event=message,           # Message или CallbackQuery
    state=fsm_context,       # FSMContext
    form_path="path.yml",    # Путь к конфигу
    initial_data={"key": "value"}  # Предзаполнение
)
```

### register_submit_handler

```python
from main.forms import register_submit_handler, FormSubmitResult

@register_submit_handler("form_id")
async def handler(data: dict, state: FormState, config: FormConfig):
    return FormSubmitResult(success=True, message="OK")
```

## 🔄 Миграция с legacy

Для использования старого flow без Form Engine:

```bash
USE_FORM_ENGINE=0 python3 main.py
```

## 📄 Лицензия

MIT License

## 🤝 Поддержка

По вопросам обращайтесь: [ваши контакты]
