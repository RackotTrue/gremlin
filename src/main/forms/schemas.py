"""
Pydantic-схемы для конфигурации форм.

Определяют структуру YAML/JSON конфигов форм:
- FormConfig — корневая конфигурация формы
- FieldConfig — конфигурация одного поля/шага
- ValidationConfig — правила валидации
- ReviewConfig — настройки экрана проверки данных
- SubmitConfig — настройки отправки
- ButtonsConfig — тексты кнопок навигации
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class FieldType(str, Enum):
    """Типы полей формы"""
    TEXT = "text"
    PHONE = "phone"
    EMAIL = "email"
    NUMBER = "number"
    SELECT = "select"
    DATE = "date"
    CONSENT = "consent"  # Согласие (да/нет)
    EMAIL_VERIFICATION = "email_verification"  # Верификация email кодом


class ValidationConfig(BaseModel):
    """Конфигурация валидации поля"""
    
    min_len: Optional[int] = Field(None, description="Минимальная длина строки")
    max_len: Optional[int] = Field(None, description="Максимальная длина строки")
    min_value: Optional[float] = Field(None, description="Минимальное значение (для number)")
    max_value: Optional[float] = Field(None, description="Максимальное значение (для number)")
    regex: Optional[str] = Field(None, description="Регулярное выражение для валидации")
    error_message: Optional[str] = Field(None, description="Кастомное сообщение об ошибке")


class FieldConfig(BaseModel):
    """Конфигурация одного поля формы"""
    
    id: str = Field(..., description="Уникальный идентификатор поля")
    type: FieldType = Field(..., description="Тип поля")
    label: str = Field(..., description="Текст вопроса/подсказки для пользователя")
    required: bool = Field(True, description="Обязательное ли поле")
    validation: Optional[ValidationConfig] = Field(None, description="Правила валидации")
    options: Optional[List[str]] = Field(None, description="Варианты для select")
    options_map: Optional[Dict[str, str]] = Field(
        None, 
        description="Маппинг callback_data -> отображаемое значение для select"
    )
    hint: Optional[str] = Field(None, description="Дополнительная подсказка под вопросом")
    default: Optional[Any] = Field(None, description="Значение по умолчанию")
    # Для email_verification
    verification_message: Optional[str] = Field(
        None,
        description="Текст сообщения при отправке кода верификации"
    )
    # Для consent
    consent_text: Optional[str] = Field(
        None,
        description="Полный текст согласия (для consent type)"
    )
    agree_button: Optional[str] = Field("Согласен ✅", description="Текст кнопки согласия")
    
    class Config:
        use_enum_values = True


class ReviewConfig(BaseModel):
    """Конфигурация экрана проверки данных"""
    
    enabled: bool = Field(True, description="Показывать ли review-экран")
    title: str = Field("Проверьте данные", description="Заголовок экрана")
    edit_button: str = Field("✏️ Изменить", description="Текст кнопки редактирования")
    confirm_button: str = Field("✅ Подтвердить", description="Текст кнопки подтверждения")


class SubmitConfig(BaseModel):
    """Конфигурация отправки формы"""
    
    button_text: str = Field("Отправить", description="Текст кнопки отправки")
    success_text: str = Field(
        "✅ Готово! Данные отправлены.",
        description="Сообщение при успешной отправке"
    )
    fail_text: str = Field(
        "❌ Не получилось отправить. Попробуйте еще раз.",
        description="Сообщение при ошибке"
    )


class ButtonsConfig(BaseModel):
    """Конфигурация текстов кнопок навигации"""
    
    back: str = Field("⬅️ Назад", description="Кнопка возврата на предыдущий шаг")
    cancel: str = Field("❌ Отмена", description="Кнопка отмены формы")
    restart: str = Field("🔄 Начать заново", description="Кнопка перезапуска формы")
    skip: str = Field("⏭ Пропустить", description="Кнопка пропуска необязательного поля")


class FormConfig(BaseModel):
    """Корневая конфигурация формы"""
    
    form_id: str = Field(..., description="Уникальный идентификатор формы")
    title: str = Field(..., description="Название формы")
    description: Optional[str] = Field(None, description="Описание формы (показывается в начале)")
    steps: List[FieldConfig] = Field(..., description="Шаги формы (поля)")
    review: ReviewConfig = Field(default_factory=ReviewConfig, description="Настройки review-экрана")
    submit: SubmitConfig = Field(default_factory=SubmitConfig, description="Настройки отправки")
    buttons: ButtonsConfig = Field(default_factory=ButtonsConfig, description="Тексты кнопок")
    
    # Метаданные
    version: str = Field("1.0", description="Версия конфигурации формы")
    
    def get_step_by_id(self, step_id: str) -> Optional[FieldConfig]:
        """Получить шаг по ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_step_index(self, step_id: str) -> int:
        """Получить индекс шага по ID. Возвращает -1 если не найден."""
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                return i
        return -1
    
    def get_required_steps(self) -> List[FieldConfig]:
        """Получить только обязательные шаги"""
        return [step for step in self.steps if step.required]
    
    @property
    def total_steps(self) -> int:
        """Общее количество шагов"""
        return len(self.steps)


class FormState(BaseModel):
    """Состояние заполнения формы пользователем"""
    
    form_id: str = Field(..., description="ID формы")
    user_id: int = Field(..., description="ID пользователя в Telegram")
    chat_id: int = Field(..., description="ID чата")
    current_step_index: int = Field(0, description="Индекс текущего шага")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Собранные данные")
    started_at: str = Field(..., description="Время начала заполнения (ISO format)")
    updated_at: str = Field(..., description="Время последнего обновления (ISO format)")
    is_completed: bool = Field(False, description="Завершена ли форма")
    is_cancelled: bool = Field(False, description="Отменена ли форма")
    # Для верификации email
    verification_code: Optional[str] = Field(None, description="Код верификации email")
    pending_email: Optional[str] = Field(None, description="Email, ожидающий верификации")
    
    def get_current_step_id(self, config: FormConfig) -> Optional[str]:
        """Получить ID текущего шага"""
        if 0 <= self.current_step_index < len(config.steps):
            return config.steps[self.current_step_index].id
        return None
    
    def is_on_review(self, config: FormConfig) -> bool:
        """Находится ли пользователь на экране review"""
        return self.current_step_index >= len(config.steps) and not self.is_completed
    
    def get_progress_text(self, config: FormConfig) -> str:
        """Текст прогресса: 'Шаг 2/6'"""
        total = config.total_steps
        current = min(self.current_step_index + 1, total)
        return f"Шаг {current}/{total}"


class FormSubmitResult(BaseModel):
    """Результат отправки формы"""
    
    success: bool = Field(..., description="Успешна ли отправка")
    message: Optional[str] = Field(None, description="Сообщение пользователю")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")
    error: Optional[str] = Field(None, description="Текст ошибки (если не успешно)")
