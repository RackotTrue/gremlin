"""
Form Engine — универсальный движок модальных форм для Telegram-ботов.

Позволяет создавать многошаговые формы через YAML/JSON конфигурацию
без правки кода. Поддерживает валидацию, навигацию, review-экран.

Использование:
```python
from main.forms import start_form, register_submit_handler

# Запуск формы
await start_form(message, state, form_path="resources/forms/activation.yml")

# Регистрация обработчика отправки
@register_submit_handler("my_form")
async def handle_submit(data, state, config):
    return FormSubmitResult(success=True)
```
"""

from main.forms.schemas import (
    FormConfig, 
    FieldConfig, 
    ValidationConfig, 
    FormState,
    FormSubmitResult,
    FieldType
)
from main.forms.engine import FormEngine, load_form, register_submit_handler
from main.forms.storage import FormStateStorage, get_memory_storage, get_fsm_storage
from main.forms.renderer import FormRenderer, create_renderer
from main.forms.validators import FormValidators, ValidationResult
from main.forms.handlers import (
    form_router, 
    FormEngineState, 
    start_form, 
    stop_form,
    get_active_engine
)

# Импортируем submit handlers для автоматической регистрации
from main.forms import submit_handlers  # noqa: F401

__all__ = [
    # Schemas
    "FormConfig",
    "FieldConfig",
    "ValidationConfig",
    "FormState",
    "FormSubmitResult",
    "FieldType",
    # Engine
    "FormEngine",
    "load_form",
    "register_submit_handler",
    # Storage
    "FormStateStorage",
    "get_memory_storage",
    "get_fsm_storage",
    # Renderer
    "FormRenderer",
    "create_renderer",
    # Validators
    "FormValidators",
    "ValidationResult",
    # Handlers
    "form_router",
    "FormEngineState",
    "start_form",
    "stop_form",
    "get_active_engine",
]
