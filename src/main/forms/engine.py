"""
Form Engine — главный модуль движка форм.

Координирует:
- Загрузку конфигурации из YAML/JSON
- Управление состоянием (через storage)
- Валидацию введённых данных
- Переходы между шагами
- Рендеринг сообщений и клавиатур
- Вызов хуков при отправке формы
"""

import os
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Awaitable, Union
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from main.forms.schemas import (
    FormConfig, FormState, FieldConfig, FieldType, FormSubmitResult
)
from main.forms.validators import FormValidators, ValidationResult, get_validator_for_field
from main.forms.storage import (
    FormStateStorage, InMemoryFormStateStorage, 
    FSMContextFormStateStorage, get_memory_storage, get_fsm_storage
)
from main.forms.renderer import FormRenderer, create_renderer
from main.config.log_config import logger


# Тип для submit handler
SubmitHandler = Callable[[Dict[str, Any], FormState, FormConfig], Awaitable[FormSubmitResult]]


class FormEngine:
    """
    Универсальный движок форм.
    
    Использование:
    ```python
    # Загрузка конфига
    engine = FormEngine.from_yaml("configs/forms/activation.yml")
    
    # Или из dict
    engine = FormEngine(config_dict)
    
    # Запуск формы для пользователя
    await engine.start(message, state)
    
    # Обработка ввода
    await engine.process_input(message, state)
    
    # Обработка callback
    await engine.process_callback(callback_query, state)
    ```
    """
    
    # Кэш загруженных конфигов
    _config_cache: Dict[str, FormConfig] = {}
    
    # Реестр submit handlers
    _submit_handlers: Dict[str, SubmitHandler] = {}
    
    def __init__(self, config: Union[FormConfig, Dict[str, Any]]):
        """
        Инициализация движка формы.
        
        :param config: FormConfig объект или dict с конфигурацией
        """
        if isinstance(config, dict):
            self.config = FormConfig.model_validate(config)
        else:
            self.config = config
        
        self.renderer = create_renderer(self.config)
        self._storage: Optional[FormStateStorage] = None
        
        # Debug mode
        self.debug = os.environ.get("FORM_DEBUG", "0") == "1"
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "FormEngine":
        """
        Загрузить конфигурацию из YAML файла.
        
        :param path: Путь к YAML файлу
        :return: FormEngine instance
        """
        path = Path(path)
        
        # Проверяем кэш
        cache_key = str(path.absolute())
        if cache_key in cls._config_cache:
            return cls(cls._config_cache[cache_key])
        
        # Загружаем файл
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        config = FormConfig.model_validate(data)
        cls._config_cache[cache_key] = config
        
        return cls(config)
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "FormEngine":
        """
        Загрузить конфигурацию из JSON файла.
        
        :param path: Путь к JSON файлу
        :return: FormEngine instance
        """
        path = Path(path)
        
        cache_key = str(path.absolute())
        if cache_key in cls._config_cache:
            return cls(cls._config_cache[cache_key])
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = FormConfig.model_validate(data)
        cls._config_cache[cache_key] = config
        
        return cls(config)
    
    @classmethod
    def register_submit_handler(cls, form_id: str, handler: SubmitHandler):
        """
        Зарегистрировать обработчик отправки формы.
        
        :param form_id: ID формы
        :param handler: Async функция (data, state, config) -> FormSubmitResult
        """
        cls._submit_handlers[form_id] = handler
        logger.info(f"Registered submit handler for form: {form_id}")
    
    @classmethod
    def clear_cache(cls):
        """Очистить кэш конфигов"""
        cls._config_cache.clear()
    
    def _get_storage(self, fsm_context: FSMContext) -> FormStateStorage:
        """Получить storage для текущего контекста"""
        return get_fsm_storage(fsm_context)
    
    async def start(
        self, 
        event: Union[Message, CallbackQuery],
        fsm_context: FSMContext,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Запустить форму для пользователя.
        
        :param event: Message или CallbackQuery
        :param fsm_context: FSM контекст aiogram
        :param initial_data: Начальные данные (для предзаполнения)
        """
        storage = self._get_storage(fsm_context)
        
        # Определяем user_id и chat_id
        if isinstance(event, Message):
            user_id = event.from_user.id
            chat_id = event.chat.id
        else:
            user_id = event.from_user.id
            chat_id = event.message.chat.id
        
        # Создаём новое состояние
        state = storage.create_new_state(
            form_id=self.config.form_id,
            user_id=user_id,
            chat_id=chat_id
        )
        
        # Предзаполняем данные если есть
        if initial_data:
            state.collected_data.update(initial_data)
        
        await storage.save_state(state)
        
        self._log_debug(f"Started form '{self.config.form_id}' for user {user_id}")
        
        # Показываем первый шаг
        await self._show_current_step(event, state)
    
    async def process_input(
        self, 
        message: Message,
        fsm_context: FSMContext
    ) -> bool:
        """
        Обработать текстовый ввод пользователя.
        
        :param message: Сообщение пользователя
        :param fsm_context: FSM контекст
        :return: True если ввод обработан, False если форма не активна
        """
        storage = self._get_storage(fsm_context)
        state = await storage.load_state(message.from_user.id, self.config.form_id)
        
        if not state or state.is_completed or state.is_cancelled:
            return False
        
        # Получаем текущий шаг
        if state.current_step_index >= len(self.config.steps):
            # Находимся на review — игнорируем текст
            return True
        
        current_step = self.config.steps[state.current_step_index]
        value = message.text
        
        self._log_debug(f"Processing input for step '{current_step.id}': {value}")
        
        # Для select и consent — текстовый ввод не обрабатываем
        if current_step.type in (FieldType.SELECT, FieldType.CONSENT):
            await message.answer(
                "Пожалуйста, используйте кнопки для выбора.",
                reply_markup=self.renderer.render_step_keyboard(
                    current_step, state, 
                    show_back=state.current_step_index > 0,
                    show_skip=not current_step.required
                )
            )
            return True
        
        # Валидируем ввод
        validator = get_validator_for_field(current_step)
        result = validator(value)
        
        if not result.is_valid:
            # Показываем ошибку и просим повторить
            await message.answer(
                self.renderer.render_validation_error(result.error),
                parse_mode="Markdown",
                reply_markup=self.renderer.render_step_keyboard(
                    current_step, state,
                    show_back=state.current_step_index > 0,
                    show_skip=not current_step.required
                )
            )
            return True
        
        # Специальная обработка для email — отправка кода верификации
        if current_step.type == FieldType.EMAIL:
            # Сохраняем email и переходим к верификации (если есть следующий шаг email_verification)
            next_step_index = state.current_step_index + 1
            if next_step_index < len(self.config.steps):
                next_step = self.config.steps[next_step_index]
                if next_step.type == FieldType.EMAIL_VERIFICATION:
                    # Сохраняем email как pending
                    state.pending_email = result.value
                    # Отправляем код
                    code = await self._send_verification_code(result.value)
                    state.verification_code = code
                    # Сохраняем email в данные
                    state.collected_data[current_step.id] = result.value
                    state.current_step_index = next_step_index
                    await storage.save_state(state)
                    await self._show_current_step(message, state)
                    return True
        
        # Специальная обработка для верификации email
        if current_step.type == FieldType.EMAIL_VERIFICATION:
            if not self._verify_code(value, state.verification_code):
                await message.answer(
                    self.renderer.render_validation_error("Неверный код. Попробуйте еще раз."),
                    parse_mode="Markdown",
                    reply_markup=self.renderer.render_step_keyboard(
                        current_step, state,
                        show_back=state.current_step_index > 0
                    )
                )
                return True
            # Код верный — очищаем временные данные
            state.verification_code = None
            state.pending_email = None
        
        # Сохраняем значение и переходим к следующему шагу
        state.collected_data[current_step.id] = result.value
        state.current_step_index += 1
        await storage.save_state(state)
        
        self._log_debug(f"Step '{current_step.id}' completed. Moving to step {state.current_step_index}")
        
        # Показываем следующий шаг или review
        await self._show_current_step(message, state)
        return True
    
    async def process_callback(
        self, 
        callback: CallbackQuery,
        fsm_context: FSMContext
    ) -> bool:
        """
        Обработать callback от inline-кнопки.
        
        :param callback: CallbackQuery
        :param fsm_context: FSM контекст
        :return: True если callback обработан
        """
        storage = self._get_storage(fsm_context)
        state = await storage.load_state(callback.from_user.id, self.config.form_id)
        
        if not state:
            await callback.answer("Форма не найдена. Начните заново.", show_alert=True)
            return False
        
        data = callback.data
        
        self._log_debug(f"Processing callback: {data}")
        
        # Обработка навигации
        if data == FormRenderer.CB_BACK:
            await self._go_back(callback, state, storage)
            return True
        
        if data == FormRenderer.CB_CANCEL:
            await self._cancel_form(callback, state, storage)
            return True
        
        if data == FormRenderer.CB_RESTART:
            await self._restart_form(callback, state, storage, fsm_context)
            return True
        
        if data == FormRenderer.CB_SKIP:
            await self._skip_step(callback, state, storage)
            return True
        
        if data == FormRenderer.CB_SUBMIT:
            await self._submit_form(callback, state, storage)
            return True
        
        if data == FormRenderer.CB_RESEND_CODE:
            await self._resend_verification_code(callback, state, storage)
            return True
        
        # Обработка редактирования с review
        if data.startswith(FormRenderer.CB_EDIT):
            step_id = data[len(FormRenderer.CB_EDIT):]
            await self._edit_step(callback, state, storage, step_id)
            return True
        
        # Обработка select
        if data.startswith(FormRenderer.CB_SELECT):
            value = data[len(FormRenderer.CB_SELECT):]
            await self._process_select(callback, state, storage, value)
            return True
        
        # Обработка consent
        if data.startswith(FormRenderer.CB_CONSENT):
            action = data[len(FormRenderer.CB_CONSENT):]
            await self._process_consent(callback, state, storage, action)
            return True
        
        await callback.answer()
        return False
    
    async def _show_current_step(
        self, 
        event: Union[Message, CallbackQuery],
        state: FormState
    ) -> None:
        """Показать текущий шаг формы"""
        # Проверяем, не на review ли мы
        if state.current_step_index >= len(self.config.steps):
            await self._show_review(event, state)
            return
        
        current_step = self.config.steps[state.current_step_index]
        
        text = self.renderer.render_step_text(current_step, state)
        keyboard = self.renderer.render_step_keyboard(
            current_step, state,
            show_back=state.current_step_index > 0,
            show_skip=not current_step.required
        )
        
        if isinstance(event, Message):
            await event.answer(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await event.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
            await event.answer()
    
    async def _show_review(
        self, 
        event: Union[Message, CallbackQuery],
        state: FormState
    ) -> None:
        """Показать экран review"""
        text = self.renderer.render_review_text(state)
        keyboard = self.renderer.render_review_keyboard(state)
        
        if isinstance(event, Message):
            await event.answer(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await event.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
            await event.answer()
    
    async def _go_back(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage
    ) -> None:
        """Вернуться на предыдущий шаг"""
        if state.current_step_index > 0:
            state.current_step_index -= 1
            
            # Пропускаем email_verification при возврате (возвращаемся сразу к email)
            if state.current_step_index < len(self.config.steps):
                current_step = self.config.steps[state.current_step_index]
                if current_step.type == FieldType.EMAIL_VERIFICATION:
                    state.current_step_index -= 1
            
            await storage.save_state(state)
        
        await self._show_current_step(callback, state)
    
    async def _cancel_form(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage
    ) -> None:
        """Отменить форму"""
        state.is_cancelled = True
        await storage.save_state(state)
        
        await callback.message.answer(self.renderer.render_cancel_text())
        await callback.answer()
        
        # Очищаем состояние
        await storage.reset_state(state.user_id, state.form_id)
    
    async def _restart_form(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage,
        fsm_context: FSMContext
    ) -> None:
        """Начать форму заново"""
        await storage.reset_state(state.user_id, state.form_id)
        await self.start(callback, fsm_context)
    
    async def _skip_step(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage
    ) -> None:
        """Пропустить необязательный шаг"""
        if state.current_step_index < len(self.config.steps):
            current_step = self.config.steps[state.current_step_index]
            if not current_step.required:
                state.collected_data[current_step.id] = None
                state.current_step_index += 1
                await storage.save_state(state)
        
        await self._show_current_step(callback, state)
    
    async def _process_select(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage,
        value: str
    ) -> None:
        """Обработать выбор из select"""
        if state.current_step_index >= len(self.config.steps):
            await callback.answer()
            return
        
        current_step = self.config.steps[state.current_step_index]
        
        # Получаем отображаемое значение
        if current_step.options_map and value in current_step.options_map:
            display_value = current_step.options_map[value]
        else:
            display_value = value
        
        state.collected_data[current_step.id] = display_value
        state.current_step_index += 1
        await storage.save_state(state)
        
        self._log_debug(f"Select '{current_step.id}' = {display_value}")
        
        await self._show_current_step(callback, state)
    
    async def _process_consent(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage,
        action: str
    ) -> None:
        """Обработать согласие"""
        if state.current_step_index >= len(self.config.steps):
            await callback.answer()
            return
        
        current_step = self.config.steps[state.current_step_index]
        
        if action == "agree":
            state.collected_data[current_step.id] = True
            state.current_step_index += 1
            await storage.save_state(state)
            
            self._log_debug(f"Consent '{current_step.id}' = True")
            
            await self._show_current_step(callback, state)
        else:
            await callback.answer("Необходимо дать согласие для продолжения", show_alert=True)
    
    async def _edit_step(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage,
        step_id: str
    ) -> None:
        """Перейти к редактированию конкретного шага"""
        step_index = self.config.get_step_index(step_id)
        if step_index >= 0:
            state.current_step_index = step_index
            await storage.save_state(state)
            await self._show_current_step(callback, state)
        else:
            await callback.answer("Шаг не найден", show_alert=True)
    
    async def _submit_form(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage
    ) -> None:
        """Отправить форму"""
        self._log_debug(f"Submitting form. Data: {state.collected_data}")
        
        # Ищем зарегистрированный handler
        handler = self._submit_handlers.get(self.config.form_id)
        
        if handler:
            try:
                result = await handler(state.collected_data, state, self.config)
                
                if result.success:
                    state.is_completed = True
                    await storage.save_state(state)
                    
                    message = result.message or self.renderer.render_success_text(state)
                    await callback.message.answer(message, parse_mode="Markdown")
                else:
                    await callback.message.answer(
                        self.renderer.render_fail_text(result.error),
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error in submit handler: {e}")
                await callback.message.answer(
                    self.renderer.render_fail_text(str(e)),
                    parse_mode="Markdown"
                )
        else:
            # Нет handler — просто помечаем как завершённую
            state.is_completed = True
            await storage.save_state(state)
            await callback.message.answer(
                self.renderer.render_success_text(state),
                parse_mode="Markdown"
            )
        
        await callback.answer()
    
    async def _send_verification_code(self, email: str) -> str:
        """
        Отправить код верификации на email.
        Возвращает сгенерированный код.
        """
        from main.service.integration.mail_service import send_checking_mail
        
        try:
            code = await send_checking_mail(email)
            self._log_debug(f"Sent verification code to {email}")
            return str(code)
        except Exception as e:
            logger.error(f"Failed to send verification code: {e}")
            # Возвращаем заглушку если не удалось отправить
            return "0000"
    
    def _verify_code(self, input_code: str, expected_code: Optional[str]) -> bool:
        """Проверить код верификации"""
        if not expected_code:
            return True  # Нет кода — пропускаем проверку
        
        try:
            return int(input_code) == int(expected_code)
        except ValueError:
            return False
    
    async def _resend_verification_code(
        self, 
        callback: CallbackQuery,
        state: FormState,
        storage: FormStateStorage
    ) -> None:
        """Повторно отправить код верификации"""
        if state.pending_email:
            code = await self._send_verification_code(state.pending_email)
            state.verification_code = code
            await storage.save_state(state)
            await callback.answer("Код отправлен повторно!", show_alert=True)
        else:
            await callback.answer("Email не найден. Вернитесь назад.", show_alert=True)
    
    def _log_debug(self, message: str):
        """Логирование в debug режиме"""
        if self.debug:
            logger.debug(f"[FormEngine:{self.config.form_id}] {message}")


# Фабричные функции для удобства
def load_form(path: Union[str, Path]) -> FormEngine:
    """
    Загрузить форму из файла (YAML или JSON).
    Автоматически определяет формат по расширению.
    """
    path = Path(path)
    
    if path.suffix in ('.yml', '.yaml'):
        return FormEngine.from_yaml(path)
    elif path.suffix == '.json':
        return FormEngine.from_json(path)
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}")


def register_submit_handler(form_id: str):
    """
    Декоратор для регистрации submit handler.
    
    Использование:
    ```python
    @register_submit_handler("activation")
    async def handle_activation(data, state, config):
        # Обработка данных формы
        return FormSubmitResult(success=True)
    ```
    """
    def decorator(func: SubmitHandler):
        FormEngine.register_submit_handler(form_id, func)
        return func
    return decorator
