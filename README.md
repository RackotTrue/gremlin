# Сетка Гармошка Bot

Telegram бот для управления гарантиями и устройствами компании Сетка Гармошка.

## Возможности

- 🔹 Активировать гарантию 📑
- 🔹 Посмотреть информацию о своих устройствах 💻
- 🔹 Получить информацию о сервисном центре 🔧
- 🔹 Посмотреть актуальные акции и предложения 📉
- 🔹 Массовая рассылка сообщений (для администраторов)

## Технологии

- Python 3.10+
- aiogram 3.21.0
- PostgreSQL (asyncpg)
- SQLAlchemy
- Dynaconf

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ.git
cd setka-garmoshka-bot
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
   - Скопируйте `src/resources/properties/application_properties.yaml.example` в `application_properties.yaml`
   - Заполните все необходимые параметры (токен бота, БД, почта и т.д.)

5. Настройте базу данных PostgreSQL:
```sql
CREATE DATABASE setka_garmoshka_db;
CREATE USER setka_garmoshka WITH ENCRYPTED PASSWORD 'ваш_пароль';
GRANT ALL PRIVILEGES ON DATABASE setka_garmoshka_db TO setka_garmoshka;
```

6. Запустите бота:
```bash
cd src
python3 main.py
```

## Структура проекта

```
setka-garmoshka-bot/
├── src/
│   ├── main/
│   │   ├── config/          # Конфигурация
│   │   ├── handler/          # Обработчики команд
│   │   ├── service/          # Бизнес-логика
│   │   ├── model/            # Модели БД
│   │   ├── repository/      # Работа с БД
│   │   ├── keyboard/         # Клавиатуры
│   │   └── state/            # FSM состояния
│   └── resources/
│       └── properties/      # Конфигурационные файлы
└── requirements.txt
```

## Команды администратора

- `/send_text` - Рассылка текста всем пользователям
- `/send_photo` - Рассылка фото с текстом
- `/send_video` - Рассылка видео с текстом
- `/device/delete` - Удаление устройства
- `/get_admin_ids` - Список ID администраторов

## Контакты

В случае возникновения неполадок свяжитесь с нами: **89858546153**

## Лицензия

Proprietary - Все права защищены
