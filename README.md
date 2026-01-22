# 🤖 Активация гарантии. Шаблон

Универсальный шаблон Telegram-бота для активации гарантий с конфигурируемыми формами.

## 🚀 Возможности

- ✅ **Универсальный Form Engine** — создание форм через YAML/JSON конфигурацию без правки кода
- ✅ **Активация гарантии** — многошаговая форма с валидацией
- ✅ **Интеграция с Bitrix24** — автоматическая отправка данных в CRM
- ✅ **PDF сертификаты** — генерация и отправка гарантийных сертификатов
- ✅ **Управление устройствами** — просмотр информации о зарегистрированных устройствах
- ✅ **Массовая рассылка** — инструменты для администраторов

## 🎯 Для кого этот шаблон?

Этот шаблон идеально подходит для:
- Компаний, продающих товары с гарантией
- Сервисных центров
- Интернет-магазинов
- Любых бизнесов, которым нужны конфигурируемые формы в Telegram

## 📦 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/RackotTrue/guarantee-activation-template.git
cd guarantee-activation-template
```

2. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте конфигурацию:
   - Отредактируйте `src/resources/properties/application_properties.yaml`
   - Заполните все необходимые параметры (токен бота, БД, почта, Bitrix24 и т.д.)

5. Настройте базу данных PostgreSQL:
```sql
CREATE DATABASE your_db_name;
CREATE USER your_db_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
```

6. Запустите бота:
```bash
cd src
python3 main.py
```

## 📝 Создание новых форм

Подробная документация по созданию форм через Form Engine находится в [README_TEMPLATE.md](README_TEMPLATE.md).

### Быстрый старт:

1. Создайте YAML-конфиг формы в `src/resources/forms/`
2. Добавьте submit handler в `src/main/forms/submit_handlers.py`
3. Подключите форму к команде через `start_form()`

Пример:
```python
from main.forms import start_form
from pathlib import Path

@router.message(Command('my_form'))
async def start_my_form(message, state):
    form_path = Path("resources/forms/my_form.yml")
    await start_form(message, state, form_path=form_path)
```

## 🏗️ Структура проекта

```
├── src/
│   ├── main/
│   │   ├── forms/              # Form Engine (универсальный движок форм)
│   │   ├── handler/            # Обработчики команд
│   │   ├── service/            # Бизнес-логика и интеграции
│   │   ├── model/              # Модели БД
│   │   ├── repository/         # Работа с БД
│   │   ├── config/             # Конфигурация
│   │   └── ...
│   └── resources/
│       ├── forms/              # YAML конфигурации форм
│       └── properties/         # Настройки приложения
├── test_form_engine.py         # Тесты Form Engine
├── README_TEMPLATE.md          # Документация для разработчиков
└── requirements.txt
```

## 🔧 Технологии

- **Python 3.10+**
- **aiogram 3.21.0** — Telegram Bot API
- **PostgreSQL** (asyncpg) — база данных
- **SQLAlchemy** — ORM
- **Dynaconf** — управление конфигурацией
- **Pydantic** — валидация данных
- **ReportLab** — генерация PDF

## 📚 Документация

- [README_TEMPLATE.md](README_TEMPLATE.md) — полная документация Form Engine
- [test_form_engine.py](test_form_engine.py) — примеры использования и тесты

## 🧪 Тестирование

Запустите smoke test для проверки Form Engine:
```bash
python3 test_form_engine.py
```

## 🔄 Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `USE_FORM_ENGINE` | Использовать Form Engine для гарантии | `1` |
| `FORM_DEBUG` | Включить debug-логирование форм | `0` |

## 📄 Лицензия

MIT License

## 🤝 Поддержка

По вопросам обращайтесь: [ваши контакты]
