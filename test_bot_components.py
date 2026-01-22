#!/usr/bin/env python3
"""Скрипт для тестирования всех компонентов бота"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к src
sys.path.append('src')

async def test_components():
    """Тестирует все компоненты бота"""
    results = []
    
    # 1. Тест конфигурации
    print("1. Проверка конфигурации...")
    try:
        from main.config.dynaconf_config import config_setting, current_environment
        assert hasattr(config_setting, 'BOT_TOKEN'), "BOT_TOKEN не найден"
        assert hasattr(config_setting, 'POSTGRES'), "POSTGRES не найден"
        assert hasattr(config_setting.POSTGRES, 'HOST'), "POSTGRES.HOST не найден"
        print("   ✅ Конфигурация загружена успешно")
        results.append(("Конфигурация", True))
    except Exception as e:
        print(f"   ❌ Ошибка конфигурации: {e}")
        results.append(("Конфигурация", False))
    
    # 2. Тест подключения к БД
    print("2. Проверка подключения к БД...")
    try:
        from main.config.db_config import create_tables, engine
        await create_tables()
        print("   ✅ Подключение к БД успешно, таблицы созданы")
        results.append(("База данных", True))
    except Exception as e:
        print(f"   ❌ Ошибка БД: {e}")
        results.append(("База данных", False))
    
    # 3. Тест подключения к Telegram API
    print("3. Проверка подключения к Telegram API...")
    try:
        from main.config.bot_config import bot
        me = await bot.get_me()
        print(f"   ✅ Бот подключен: {me.first_name} (@{me.username})")
        results.append(("Telegram API", True))
    except Exception as e:
        print(f"   ❌ Ошибка Telegram API: {e}")
        results.append(("Telegram API", False))
    
    # 4. Тест импорта роутеров
    print("4. Проверка роутеров...")
    try:
        from main.handler.main_handler import router as main_router
        from main.handler.administration_handler import router as admin_router
        from main.handler.guarantee_handler import router as guarantee_router
        from main.handler.promotion_handler import router as promotion_router
        from main.handler.device_info_handler import router as device_info_router
        from main.handler.technical_department_handler import router as technical_department_router
        from main.handler.broadcast_handler import router as broadcast_router
        print("   ✅ Все роутеры импортированы успешно")
        results.append(("Роутеры", True))
    except Exception as e:
        print(f"   ❌ Ошибка роутеров: {e}")
        results.append(("Роутеры", False))
    
    # 5. Тест конфигурации Bitrix24
    print("5. Проверка конфигурации Bitrix24...")
    try:
        from main.config.bitrix24_config import WEBHOOK, DEAL_CATEGORY_ID_GUARANTEE_MP
        assert WEBHOOK, "WEBHOOK не настроен"
        assert DEAL_CATEGORY_ID_GUARANTEE_MP, "DEAL_CATEGORY_ID_GUARANTEE_MP не настроен"
        print(f"   ✅ Bitrix24 настроен: webhook={WEBHOOK[:30]}...")
        results.append(("Bitrix24", True))
    except Exception as e:
        print(f"   ❌ Ошибка Bitrix24: {e}")
        results.append(("Bitrix24", False))
    
    # 6. Тест конфигурации почты
    print("6. Проверка конфигурации почты...")
    try:
        from main.config.mail_config import SMTP_SERVER, SMTP_PORT, EMAIL_SENDER_ADDRESS
        assert SMTP_SERVER, "SMTP_SERVER не настроен"
        assert SMTP_PORT, "SMTP_PORT не настроен"
        print(f"   ✅ Почта настроена: {SMTP_SERVER}:{SMTP_PORT}")
        results.append(("Почта", True))
    except Exception as e:
        print(f"   ❌ Ошибка почты: {e}")
        results.append(("Почта", False))
    
    # 7. Тест сервисов
    print("7. Проверка сервисов...")
    try:
        from main.service.integration.notifications_service import setup_scheduled_jobs
        from main.service.model.user_service import UserService
        from main.service.model.device_service import DeviceService
        from main.service.model.guarantee_service import GuaranteeService
        print("   ✅ Все сервисы импортированы успешно")
        results.append(("Сервисы", True))
    except Exception as e:
        print(f"   ❌ Ошибка сервисов: {e}")
        results.append(("Сервисы", False))
    
    # Итоги
    print("\n" + "="*50)
    print("ИТОГИ ТЕСТИРОВАНИЯ:")
    print("="*50)
    passed = sum(1 for _, status in results if status)
    total = len(results)
    for name, status in results:
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {name}")
    print(f"\nПройдено: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены успешно! Бот готов к работе.")
    else:
        print(f"\n⚠️  Обнаружены проблемы: {total - passed} компонентов не работают")
    
    return passed == total

if __name__ == '__main__':
    success = asyncio.run(test_components())
    sys.exit(0 if success else 1)
