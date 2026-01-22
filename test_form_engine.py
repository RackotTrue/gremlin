#!/usr/bin/env python3
"""
Smoke Test для Form Engine.

Проверяет:
1. Загрузку конфигурации форм из YAML
2. Валидаторы полей
3. Рендеринг сообщений
4. State management

Запуск: python3 test_form_engine.py
"""

import sys
import asyncio
from pathlib import Path

# Добавляем src в путь
src_path = Path(__file__).resolve().parent / 'src'
sys.path.insert(0, str(src_path))


def test_schemas():
    """Тест загрузки и валидации схем"""
    print("📋 Тест: Schemas...")
    
    # Импортируем напрямую из schemas, без __init__.py
    # чтобы избежать инициализации бота
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
    
    from main.forms.schemas import (
        FormConfig, FieldConfig, FieldType, 
        ValidationConfig, FormState
    )
    
    # Тест создания FieldConfig
    field = FieldConfig(
        id="test_field",
        type=FieldType.TEXT,
        label="Test question",
        required=True,
        validation=ValidationConfig(min_len=2, max_len=50)
    )
    assert field.id == "test_field"
    assert field.type == FieldType.TEXT
    print("  ✅ FieldConfig OK")
    
    # Тест создания FormConfig
    config = FormConfig(
        form_id="test_form",
        title="Test Form",
        steps=[field]
    )
    assert config.form_id == "test_form"
    assert len(config.steps) == 1
    assert config.total_steps == 1
    print("  ✅ FormConfig OK")
    
    # Тест FormState
    state = FormState(
        form_id="test_form",
        user_id=123,
        chat_id=456,
        started_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    assert state.current_step_index == 0
    assert not state.is_completed
    print("  ✅ FormState OK")
    
    print("✅ Schemas: OK\n")


def test_validators():
    """Тест валидаторов"""
    print("🔍 Тест: Validators...")
    
    # Импортируем напрямую без __init__.py
    from main.forms.validators import FormValidators, ValidationResult
    from main.forms.schemas import FieldConfig, FieldType, ValidationConfig
    
    # Тест валидации телефона
    phone_field = FieldConfig(
        id="phone", type=FieldType.PHONE, label="Phone", required=True
    )
    
    result = FormValidators.validate("+79991234567", phone_field)
    assert result.is_valid
    assert result.value == "+79991234567"
    print("  ✅ Phone validation OK")
    
    result = FormValidators.validate("89991234567", phone_field)
    assert result.is_valid
    assert result.value == "+79991234567"  # Нормализация 8 -> +7
    print("  ✅ Phone normalization OK")
    
    result = FormValidators.validate("123", phone_field)
    assert not result.is_valid
    print("  ✅ Phone rejection OK")
    
    # Тест валидации email
    email_field = FieldConfig(
        id="email", type=FieldType.EMAIL, label="Email", required=True
    )
    
    result = FormValidators.validate("test@example.com", email_field)
    assert result.is_valid
    print("  ✅ Email validation OK")
    
    result = FormValidators.validate("invalid-email", email_field)
    assert not result.is_valid
    print("  ✅ Email rejection OK")
    
    # Тест валидации текста с regex
    name_field = FieldConfig(
        id="name", type=FieldType.TEXT, label="Name", required=True,
        validation=ValidationConfig(
            min_len=2,
            regex=r"^[A-Za-zА-Яа-яЁё]+(?:-[A-Za-zА-Яа-яЁё]+)*$"
        )
    )
    
    result = FormValidators.validate("Иван", name_field)
    assert result.is_valid
    print("  ✅ Text validation OK")
    
    result = FormValidators.validate("123", name_field)
    assert not result.is_valid
    print("  ✅ Text regex rejection OK")
    
    # Тест валидации даты
    date_field = FieldConfig(
        id="date", type=FieldType.DATE, label="Date", required=True
    )
    
    result = FormValidators.validate("15.01.2024", date_field)
    assert result.is_valid
    print("  ✅ Date validation OK")
    
    result = FormValidators.validate("2024-01-15", date_field)
    assert not result.is_valid
    print("  ✅ Date format rejection OK")
    
    # Тест необязательного поля
    optional_field = FieldConfig(
        id="optional", type=FieldType.TEXT, label="Optional", required=False
    )
    
    result = FormValidators.validate("", optional_field)
    assert result.is_valid
    assert result.value is None
    print("  ✅ Optional field OK")
    
    print("✅ Validators: OK\n")


def test_yaml_loading():
    """Тест загрузки YAML конфигурации"""
    print("📄 Тест: YAML Loading...")
    
    from main.forms.engine import FormEngine
    from main.forms.schemas import FormConfig
    
    yaml_path = Path(__file__).resolve().parent / 'src' / 'resources' / 'forms' / 'activation.yml'
    
    if not yaml_path.exists():
        print(f"  ⚠️ Файл не найден: {yaml_path}")
        print("  ⏭ Пропускаем тест YAML\n")
        return
    
    engine = FormEngine.from_yaml(yaml_path)
    
    assert engine.config.form_id == "activation"
    assert engine.config.title == "Активация гарантии"
    assert len(engine.config.steps) > 0
    print(f"  ✅ Загружено шагов: {len(engine.config.steps)}")
    
    # Проверяем типы шагов
    step_types = [step.type for step in engine.config.steps]
    print(f"  ✅ Типы шагов: {step_types}")
    
    # Проверяем review config
    assert engine.config.review.enabled
    print("  ✅ Review enabled")
    
    print("✅ YAML Loading: OK\n")


def test_renderer():
    """Тест рендеринга сообщений"""
    print("🎨 Тест: Renderer...")
    
    from main.forms.renderer import FormRenderer
    from main.forms.schemas import (
        FormConfig, FieldConfig, FieldType, FormState
    )
    
    # Создаём тестовую форму
    config = FormConfig(
        form_id="test",
        title="Test Form",
        steps=[
            FieldConfig(id="name", type=FieldType.TEXT, label="Ваше имя?", required=True),
            FieldConfig(
                id="category", type=FieldType.SELECT, label="Категория?",
                required=True, options=["A", "B", "C"]
            ),
        ]
    )
    
    renderer = FormRenderer(config)
    
    # Создаём состояние
    state = FormState(
        form_id="test",
        user_id=123,
        chat_id=456,
        current_step_index=0,
        started_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    # Тест рендеринга текста шага
    step = config.steps[0]
    text = renderer.render_step_text(step, state)
    assert "Шаг 1/2" in text
    assert "Ваше имя?" in text
    print("  ✅ Step text rendering OK")
    
    # Тест рендеринга клавиатуры
    keyboard = renderer.render_step_keyboard(step, state, show_back=False)
    assert keyboard is not None
    print("  ✅ Keyboard rendering OK")
    
    # Тест рендеринга select
    select_step = config.steps[1]
    state.current_step_index = 1
    keyboard = renderer.render_step_keyboard(select_step, state, show_back=True)
    # Должны быть кнопки A, B, C + навигация
    button_count = sum(len(row) for row in keyboard.inline_keyboard)
    assert button_count >= 3
    print(f"  ✅ Select buttons: {button_count}")
    
    # Тест рендеринга review
    state.collected_data = {"name": "Тест", "category": "A"}
    state.current_step_index = 2  # После последнего шага
    review_text = renderer.render_review_text(state)
    assert "Тест" in review_text
    print("  ✅ Review rendering OK")
    
    print("✅ Renderer: OK\n")


def test_storage():
    """Тест хранилища состояния"""
    print("💾 Тест: Storage...")
    
    from main.forms.storage import InMemoryFormStateStorage
    from main.forms.schemas import FormState
    
    storage = InMemoryFormStateStorage()
    
    # Создаём состояние
    state = storage.create_new_state("test_form", user_id=123, chat_id=456)
    assert state.form_id == "test_form"
    assert state.current_step_index == 0
    print("  ✅ State creation OK")
    
    # Сохраняем
    asyncio.run(storage.save_state(state))
    
    # Загружаем
    loaded = asyncio.run(storage.load_state(123, "test_form"))
    assert loaded is not None
    assert loaded.form_id == "test_form"
    print("  ✅ State save/load OK")
    
    # Проверяем exists
    exists = asyncio.run(storage.exists(123, "test_form"))
    assert exists
    print("  ✅ State exists OK")
    
    # Сбрасываем
    asyncio.run(storage.reset_state(123, "test_form"))
    exists = asyncio.run(storage.exists(123, "test_form"))
    assert not exists
    print("  ✅ State reset OK")
    
    print("✅ Storage: OK\n")


def test_submit_handlers():
    """Тест регистрации submit handlers"""
    print("📤 Тест: Submit Handlers...")
    
    from main.forms.engine import FormEngine, register_submit_handler
    from main.forms.schemas import FormSubmitResult
    
    # Регистрируем тестовый handler
    @register_submit_handler("test_submit")
    async def test_handler(data, state, config):
        return FormSubmitResult(success=True, message="Test OK")
    
    # Проверяем, что handler зарегистрирован
    assert "test_submit" in FormEngine._submit_handlers
    print("  ✅ Handler registration OK")
    
    # Пропускаем проверку activation handler, т.к. он зависит от bot_config
    print("  ⏭ Activation handler test skipped (requires bot token)")
    
    print("✅ Submit Handlers: OK\n")


def main():
    print("=" * 60)
    print("🧪 Form Engine Smoke Test")
    print("=" * 60 + "\n")
    
    try:
        test_schemas()
        test_validators()
        test_yaml_loading()
        test_renderer()
        test_storage()
        test_submit_handlers()
        
        print("=" * 60)
        print("✅ Все тесты пройдены успешно!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Тест провален: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
