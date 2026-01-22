"""
Renderer — генерация сообщений и клавиатур из конфигурации формы.

Отвечает за:
- Рендеринг текста шага (вопрос + подсказка + прогресс)
- Генерация inline-клавиатур (для select, consent, навигации)
- Рендеринг review-экрана
- Форматирование собранных данных
"""

from typing import Optional, List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from main.forms.schemas import (
    FormConfig, FormState, FieldConfig, FieldType,
    ReviewConfig, ButtonsConfig
)


class FormRenderer:
    """Рендерер сообщений и клавиатур для Form Engine"""
    
    # Префиксы для callback_data
    CB_PREFIX = "form_"
    CB_SELECT = f"{CB_PREFIX}select_"
    CB_CONSENT = f"{CB_PREFIX}consent_"
    CB_BACK = f"{CB_PREFIX}back"
    CB_CANCEL = f"{CB_PREFIX}cancel"
    CB_RESTART = f"{CB_PREFIX}restart"
    CB_SKIP = f"{CB_PREFIX}skip"
    CB_SUBMIT = f"{CB_PREFIX}submit"
    CB_EDIT = f"{CB_PREFIX}edit_"
    CB_RESEND_CODE = f"{CB_PREFIX}resend_code"
    
    def __init__(self, config: FormConfig):
        self.config = config
    
    def render_step_text(
        self, 
        step: FieldConfig, 
        state: FormState,
        show_progress: bool = True
    ) -> str:
        """
        Рендерит текст сообщения для шага формы.
        
        :param step: Конфигурация текущего шага
        :param state: Текущее состояние формы
        :param show_progress: Показывать ли прогресс
        :return: Отформатированный текст
        """
        parts = []
        
        # Прогресс
        if show_progress:
            progress = state.get_progress_text(self.config)
            parts.append(f"📝 *{progress}*\n")
        
        # Основной вопрос/label
        parts.append(step.label)
        
        # Подсказка (hint)
        if step.hint:
            parts.append(f"\n\n_{step.hint}_")
        
        # Для consent — показываем полный текст согласия
        if step.type == FieldType.CONSENT and step.consent_text:
            parts.append(f"\n\n{step.consent_text}")
        
        return "\n".join(parts) if len(parts) > 1 else parts[0]
    
    def render_step_keyboard(
        self, 
        step: FieldConfig,
        state: FormState,
        show_back: bool = True,
        show_cancel: bool = True,
        show_skip: bool = False
    ) -> InlineKeyboardMarkup:
        """
        Генерирует клавиатуру для шага формы.
        
        :param step: Конфигурация текущего шага
        :param state: Текущее состояние формы
        :param show_back: Показывать кнопку "Назад"
        :param show_cancel: Показывать кнопку "Отмена"
        :param show_skip: Показывать кнопку "Пропустить"
        :return: InlineKeyboardMarkup
        """
        buttons = self.config.buttons
        keyboard_rows: List[List[InlineKeyboardButton]] = []
        
        # Специфичные кнопки для типа поля
        if step.type == FieldType.SELECT:
            keyboard_rows.extend(self._render_select_buttons(step))
        
        elif step.type == FieldType.CONSENT:
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=step.agree_button or "Согласен ✅",
                    callback_data=f"{self.CB_CONSENT}agree"
                )
            ])
        
        elif step.type == FieldType.EMAIL_VERIFICATION:
            # Кнопка повторной отправки кода
            keyboard_rows.append([
                InlineKeyboardButton(
                    text="📧 Отправить код повторно",
                    callback_data=self.CB_RESEND_CODE
                )
            ])
        
        # Навигационные кнопки
        nav_row: List[InlineKeyboardButton] = []
        
        # Кнопка "Назад" (не на первом шаге)
        if show_back and state.current_step_index > 0:
            nav_row.append(InlineKeyboardButton(
                text=buttons.back,
                callback_data=self.CB_BACK
            ))
        
        # Кнопка "Пропустить" (для необязательных полей)
        if show_skip and not step.required:
            nav_row.append(InlineKeyboardButton(
                text=buttons.skip,
                callback_data=self.CB_SKIP
            ))
        
        if nav_row:
            keyboard_rows.append(nav_row)
        
        # Кнопка "Отмена" (отдельной строкой)
        if show_cancel:
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=buttons.cancel,
                    callback_data=self.CB_CANCEL
                )
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    def _render_select_buttons(self, step: FieldConfig) -> List[List[InlineKeyboardButton]]:
        """Генерирует кнопки для поля типа select"""
        rows = []
        
        # Используем options_map если есть, иначе options
        if step.options_map:
            for callback_key, display_value in step.options_map.items():
                rows.append([
                    InlineKeyboardButton(
                        text=display_value,
                        callback_data=f"{self.CB_SELECT}{callback_key}"
                    )
                ])
        elif step.options:
            for option in step.options:
                rows.append([
                    InlineKeyboardButton(
                        text=option,
                        callback_data=f"{self.CB_SELECT}{option}"
                    )
                ])
        
        return rows
    
    def render_review_text(self, state: FormState) -> str:
        """
        Рендерит экран проверки данных (review).
        
        :param state: Состояние формы с собранными данными
        :return: Отформатированный текст
        """
        review = self.config.review
        parts = [f"*{review.title}*\n"]
        
        # Список собранных данных
        for step in self.config.steps:
            value = state.collected_data.get(step.id)
            
            # Пропускаем технические поля (верификационный код и т.п.)
            if step.type == FieldType.EMAIL_VERIFICATION:
                continue
            
            # Форматируем значение
            display_value = self._format_value(value, step)
            
            # Добавляем строку с названием поля и значением
            # Убираем эмодзи из label для чистоты
            clean_label = step.label.split('\n')[0].strip()
            if clean_label.endswith('?'):
                clean_label = clean_label[:-1]
            if clean_label.endswith(':'):
                clean_label = clean_label[:-1]
            
            parts.append(f"• *{clean_label}:* {display_value}")
        
        return "\n".join(parts)
    
    def _format_value(self, value: Any, step: FieldConfig) -> str:
        """Форматирует значение для отображения"""
        if value is None:
            return "_не указано_"
        
        if step.type == FieldType.CONSENT:
            return "✅ Да" if value else "❌ Нет"
        
        if isinstance(value, bool):
            return "Да" if value else "Нет"
        
        return str(value)
    
    def render_review_keyboard(self, state: FormState) -> InlineKeyboardMarkup:
        """
        Генерирует клавиатуру для экрана review.
        
        :param state: Состояние формы
        :return: InlineKeyboardMarkup с кнопками редактирования и отправки
        """
        review = self.config.review
        submit = self.config.submit
        buttons = self.config.buttons
        
        keyboard_rows: List[List[InlineKeyboardButton]] = []
        
        # Кнопки редактирования каждого поля
        edit_row: List[InlineKeyboardButton] = []
        for i, step in enumerate(self.config.steps):
            # Пропускаем технические поля
            if step.type == FieldType.EMAIL_VERIFICATION:
                continue
            
            # Короткое название для кнопки
            short_label = step.label.split('\n')[0][:15].strip()
            if len(short_label) < len(step.label.split('\n')[0]):
                short_label += "..."
            
            edit_row.append(InlineKeyboardButton(
                text=f"✏️ {short_label}",
                callback_data=f"{self.CB_EDIT}{step.id}"
            ))
            
            # По 2 кнопки в ряд
            if len(edit_row) == 2:
                keyboard_rows.append(edit_row)
                edit_row = []
        
        if edit_row:
            keyboard_rows.append(edit_row)
        
        # Кнопка "Отправить"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=submit.button_text,
                callback_data=self.CB_SUBMIT
            )
        ])
        
        # Кнопка "Начать заново"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=buttons.restart,
                callback_data=self.CB_RESTART
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    def render_success_text(self, state: FormState) -> str:
        """Текст успешной отправки"""
        return self.config.submit.success_text
    
    def render_fail_text(self, error: Optional[str] = None) -> str:
        """Текст ошибки отправки"""
        base = self.config.submit.fail_text
        if error:
            return f"{base}\n\n_Ошибка: {error}_"
        return base
    
    def render_cancel_text(self) -> str:
        """Текст отмены формы"""
        return "❌ Заполнение формы отменено."
    
    def render_intro_text(self) -> str:
        """Текст вступления (перед первым шагом)"""
        parts = [f"*{self.config.title}*"]
        
        if self.config.description:
            parts.append(f"\n{self.config.description}")
        
        return "\n".join(parts)
    
    def render_validation_error(self, error: str) -> str:
        """Форматирует сообщение об ошибке валидации"""
        return f"❌ {error}\n\nПожалуйста, попробуйте еще раз."


def create_renderer(config: FormConfig) -> FormRenderer:
    """Фабричная функция для создания рендерера"""
    return FormRenderer(config)
