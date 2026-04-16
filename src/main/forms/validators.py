"""
Универсальные валидаторы для Form Engine.

Каждый валидатор принимает значение и конфигурацию поля,
возвращает (is_valid, normalized_value, error_message).
"""

import re
from typing import Tuple, Optional, Any
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

from main.forms.schemas import FieldConfig, FieldType, ValidationConfig


class ValidationResult:
    """Результат валидации"""
    
    def __init__(
        self, 
        is_valid: bool, 
        value: Any = None, 
        error: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.value = value  # Нормализованное значение
        self.error = error
    
    @classmethod
    def success(cls, value: Any) -> "ValidationResult":
        return cls(is_valid=True, value=value)
    
    @classmethod
    def failure(cls, error: str) -> "ValidationResult":
        return cls(is_valid=False, error=error)


class FormValidators:
    """Набор валидаторов для разных типов полей"""
    
    # Дефолтные сообщения об ошибках
    DEFAULT_ERRORS = {
        "required": "Это поле обязательно для заполнения",
        "min_len": "Слишком короткое значение. Минимум {min_len} символов",
        "max_len": "Слишком длинное значение. Максимум {max_len} символов",
        "min_value": "Значение должно быть не меньше {min_value}",
        "max_value": "Значение должно быть не больше {max_value}",
        "regex": "Неверный формат",
        "phone": "Введите корректный номер телефона в формате +7XXXXXXXXXX",
        "email": "Введите корректный email адрес",
        "date": "Введите дату в формате ДД.ММ.ГГГГ",
        "date_range": "Дата должна быть не раньше 01.01.1900 и не позже сегодняшнего дня",
        "number": "Введите число",
        "name": "Допускаются только буквы и дефис",
        "select": "Выберите один из предложенных вариантов",
    }
    
    @classmethod
    def validate(cls, value: Any, field: FieldConfig) -> ValidationResult:
        """
        Главный метод валидации — выбирает валидатор по типу поля.
        
        :param value: Введённое пользователем значение
        :param field: Конфигурация поля
        :return: ValidationResult с результатом
        """
        # Проверка на пустое значение
        if value is None or (isinstance(value, str) and not value.strip()):
            if field.required:
                return ValidationResult.failure(cls.DEFAULT_ERRORS["required"])
            else:
                return ValidationResult.success(None)
        
        # Приводим к строке, если это текстовое поле
        if isinstance(value, str):
            value = value.strip()
        
        # Выбираем валидатор по типу
        validators = {
            FieldType.TEXT: cls._validate_text,
            FieldType.PHONE: cls._validate_phone,
            FieldType.EMAIL: cls._validate_email,
            FieldType.NUMBER: cls._validate_number,
            FieldType.SELECT: cls._validate_select,
            FieldType.DATE: cls._validate_date,
            FieldType.CONSENT: cls._validate_consent,
            FieldType.EMAIL_VERIFICATION: cls._validate_email_verification_code,
        }
        
        validator = validators.get(field.type, cls._validate_text)
        return validator(value, field)
    
    @classmethod
    def _validate_text(cls, value: str, field: FieldConfig) -> ValidationResult:
        """Валидация текстового поля"""
        validation = field.validation or ValidationConfig()
        
        # Проверка минимальной длины
        if validation.min_len and len(value) < validation.min_len:
            error = validation.error_message or cls.DEFAULT_ERRORS["min_len"].format(
                min_len=validation.min_len
            )
            return ValidationResult.failure(error)
        
        # Проверка максимальной длины
        if validation.max_len and len(value) > validation.max_len:
            error = validation.error_message or cls.DEFAULT_ERRORS["max_len"].format(
                max_len=validation.max_len
            )
            return ValidationResult.failure(error)
        
        # Проверка regex
        if validation.regex:
            if not re.fullmatch(validation.regex, value):
                error = validation.error_message or cls.DEFAULT_ERRORS["regex"]
                return ValidationResult.failure(error)
        
        return ValidationResult.success(value)
    
    @classmethod
    def _validate_phone(cls, value: str, field: FieldConfig) -> ValidationResult:
        """Валидация номера телефона (формат +7XXXXXXXXXX)"""
        # Убираем пробелы и скобки
        normalized = re.sub(r'[\s\(\)\-]', '', value)
        
        # Проверяем формат +7 и 10 цифр после
        if not re.fullmatch(r'^\+7\d{10}$', normalized):
            # 79161234567 (из Telegram contact и т.п.)
            if re.fullmatch(r'^7\d{10}$', normalized):
                normalized = '+' + normalized
            # Пробуем преобразовать 8... в +7...
            elif re.fullmatch(r'^8\d{10}$', normalized):
                normalized = '+7' + normalized[1:]
            else:
                error = (field.validation and field.validation.error_message) or cls.DEFAULT_ERRORS["phone"]
                return ValidationResult.failure(error)
        
        return ValidationResult.success(normalized)
    
    @classmethod
    def _validate_email(cls, value: str, field: FieldConfig) -> ValidationResult:
        """Валидация email"""
        try:
            # check_deliverability=False — не проверяем DNS, только формат
            valid = validate_email(value, check_deliverability=False)
            return ValidationResult.success(valid.normalized)
        except EmailNotValidError:
            error = (field.validation and field.validation.error_message) or cls.DEFAULT_ERRORS["email"]
            return ValidationResult.failure(error)
    
    @classmethod
    def _validate_number(cls, value: Any, field: FieldConfig) -> ValidationResult:
        """Валидация числового поля"""
        try:
            # Пробуем преобразовать в число
            if isinstance(value, str):
                value = value.replace(',', '.')
                num = float(value) if '.' in value else int(value)
            else:
                num = value
        except (ValueError, TypeError):
            error = (field.validation and field.validation.error_message) or cls.DEFAULT_ERRORS["number"]
            return ValidationResult.failure(error)
        
        validation = field.validation or ValidationConfig()
        
        # Проверка минимального значения
        if validation.min_value is not None and num < validation.min_value:
            error = validation.error_message or cls.DEFAULT_ERRORS["min_value"].format(
                min_value=validation.min_value
            )
            return ValidationResult.failure(error)
        
        # Проверка максимального значения
        if validation.max_value is not None and num > validation.max_value:
            error = validation.error_message or cls.DEFAULT_ERRORS["max_value"].format(
                max_value=validation.max_value
            )
            return ValidationResult.failure(error)
        
        return ValidationResult.success(num)
    
    @classmethod
    def _validate_select(cls, value: str, field: FieldConfig) -> ValidationResult:
        """Валидация выбора из списка"""
        # Проверяем, есть ли значение в options или options_map
        if field.options and value in field.options:
            return ValidationResult.success(value)
        
        if field.options_map and value in field.options_map.values():
            return ValidationResult.success(value)
        
        # Проверяем callback_data (может прийти как ключ из options_map)
        if field.options_map and value in field.options_map:
            return ValidationResult.success(field.options_map[value])
        
        error = (field.validation and field.validation.error_message) or cls.DEFAULT_ERRORS["select"]
        return ValidationResult.failure(error)
    
    @classmethod
    def _validate_date(cls, value: str, field: FieldConfig) -> ValidationResult:
        """Валидация даты (формат ДД.ММ.ГГГГ)"""
        # Проверяем формат
        if not re.fullmatch(r'^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(\d{4})$', value):
            error = (field.validation and field.validation.error_message) or cls.DEFAULT_ERRORS["date"]
            return ValidationResult.failure(error)
        
        try:
            date = datetime.strptime(value, "%d.%m.%Y").date()
            
            # Проверяем диапазон
            min_date = datetime(1900, 1, 1).date()
            today = datetime.today().date()
            
            if not (min_date <= date <= today):
                error = (field.validation and field.validation.error_message) or cls.DEFAULT_ERRORS["date_range"]
                return ValidationResult.failure(error)
            
            return ValidationResult.success(value)
        
        except ValueError:
            error = (field.validation and field.validation.error_message) or cls.DEFAULT_ERRORS["date"]
            return ValidationResult.failure(error)
    
    @classmethod
    def _validate_consent(cls, value: Any, field: FieldConfig) -> ValidationResult:
        """Валидация согласия (ожидаем True или callback 'agree')"""
        if value in [True, "agree", "yes", "да", "1"]:
            return ValidationResult.success(True)
        
        if field.required:
            return ValidationResult.failure("Необходимо дать согласие для продолжения")
        
        return ValidationResult.success(False)
    
    @classmethod
    def _validate_email_verification_code(cls, value: str, field: FieldConfig) -> ValidationResult:
        """Валидация кода верификации email (4-6 цифр)"""
        if not re.fullmatch(r'^\d{4,6}$', str(value)):
            return ValidationResult.failure("Код должен содержать 4-6 цифр")
        
        return ValidationResult.success(str(value))
    
    @classmethod
    def validate_name(cls, value: str) -> ValidationResult:
        """
        Специализированный валидатор для имени/фамилии.
        Используется для полей с id='name', 'surname' и т.п.
        """
        if not re.fullmatch(r'^[A-Za-zА-Яа-яЁё]+(?:-[A-Za-zА-Яа-яЁё]+)*$', value):
            return ValidationResult.failure(cls.DEFAULT_ERRORS["name"])
        return ValidationResult.success(value)


def get_validator_for_field(field: FieldConfig):
    """
    Возвращает функцию-валидатор для конкретного поля.
    Учитывает специальные правила для полей с определёнными ID.
    """
    def validator(value: Any) -> ValidationResult:
        # Специальные валидаторы для известных полей
        if field.id in ('name', 'surname', 'first_name', 'last_name'):
            # Сначала базовая проверка
            result = FormValidators.validate(value, field)
            if not result.is_valid:
                return result
            # Затем проверка на имя
            return FormValidators.validate_name(value)
        
        # Общий валидатор
        return FormValidators.validate(value, field)
    
    return validator
