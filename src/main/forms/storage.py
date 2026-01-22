"""
Storage для состояния форм.

Поддерживает:
- In-memory хранение (для разработки)
- aiogram FSMContext (интеграция с существующим ботом)
- PostgreSQL (для продакшена — персистентность)

Интерфейс абстрагирует хранилище, позволяя легко переключаться.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import json

from aiogram.fsm.context import FSMContext

from main.forms.schemas import FormState, FormConfig
from main.config.log_config import logger


class FormStateStorage(ABC):
    """Абстрактный интерфейс хранилища состояния форм"""
    
    @abstractmethod
    async def load_state(self, user_id: int, form_id: str) -> Optional[FormState]:
        """Загрузить состояние формы для пользователя"""
        pass
    
    @abstractmethod
    async def save_state(self, state: FormState) -> None:
        """Сохранить состояние формы"""
        pass
    
    @abstractmethod
    async def reset_state(self, user_id: int, form_id: str) -> None:
        """Сбросить состояние формы (удалить)"""
        pass
    
    @abstractmethod
    async def exists(self, user_id: int, form_id: str) -> bool:
        """Проверить, существует ли состояние"""
        pass
    
    def create_new_state(
        self, 
        form_id: str, 
        user_id: int, 
        chat_id: int
    ) -> FormState:
        """Создать новое состояние формы"""
        now = datetime.utcnow().isoformat()
        return FormState(
            form_id=form_id,
            user_id=user_id,
            chat_id=chat_id,
            current_step_index=0,
            collected_data={},
            started_at=now,
            updated_at=now,
            is_completed=False,
            is_cancelled=False
        )


class InMemoryFormStateStorage(FormStateStorage):
    """
    In-memory хранилище для состояния форм.
    Используется для разработки и тестирования.
    Данные теряются при перезапуске бота.
    """
    
    def __init__(self):
        self._storage: Dict[str, FormState] = {}
    
    def _make_key(self, user_id: int, form_id: str) -> str:
        return f"{user_id}:{form_id}"
    
    async def load_state(self, user_id: int, form_id: str) -> Optional[FormState]:
        key = self._make_key(user_id, form_id)
        return self._storage.get(key)
    
    async def save_state(self, state: FormState) -> None:
        key = self._make_key(state.user_id, state.form_id)
        state.updated_at = datetime.utcnow().isoformat()
        self._storage[key] = state
    
    async def reset_state(self, user_id: int, form_id: str) -> None:
        key = self._make_key(user_id, form_id)
        self._storage.pop(key, None)
    
    async def exists(self, user_id: int, form_id: str) -> bool:
        key = self._make_key(user_id, form_id)
        return key in self._storage


class FSMContextFormStateStorage(FormStateStorage):
    """
    Хранилище на базе aiogram FSMContext.
    Интегрируется с существующей инфраструктурой бота.
    Состояние хранится в том же месте, что и aiogram FSM state.
    """
    
    FORM_STATE_KEY = "form_engine_state"
    
    def __init__(self, fsm_context: FSMContext):
        self._ctx = fsm_context
    
    async def load_state(self, user_id: int, form_id: str) -> Optional[FormState]:
        data = await self._ctx.get_data()
        state_data = data.get(self.FORM_STATE_KEY)
        
        if not state_data:
            return None
        
        try:
            state = FormState.model_validate(state_data)
            # Проверяем, что это нужная форма
            if state.form_id != form_id:
                return None
            return state
        except Exception as e:
            logger.warning(f"Failed to load form state: {e}")
            return None
    
    async def save_state(self, state: FormState) -> None:
        state.updated_at = datetime.utcnow().isoformat()
        await self._ctx.update_data({
            self.FORM_STATE_KEY: state.model_dump()
        })
    
    async def reset_state(self, user_id: int, form_id: str) -> None:
        data = await self._ctx.get_data()
        if self.FORM_STATE_KEY in data:
            data.pop(self.FORM_STATE_KEY)
            await self._ctx.set_data(data)
    
    async def exists(self, user_id: int, form_id: str) -> bool:
        state = await self.load_state(user_id, form_id)
        return state is not None


class DatabaseFormStateStorage(FormStateStorage):
    """
    Хранилище состояния форм в PostgreSQL.
    Обеспечивает персистентность между перезапусками бота.
    
    Требует таблицу form_states:
    
    CREATE TABLE form_states (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        form_id VARCHAR(100) NOT NULL,
        chat_id BIGINT NOT NULL,
        current_step_index INTEGER DEFAULT 0,
        collected_data JSONB DEFAULT '{}',
        started_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL,
        is_completed BOOLEAN DEFAULT FALSE,
        is_cancelled BOOLEAN DEFAULT FALSE,
        verification_code VARCHAR(10),
        pending_email VARCHAR(255),
        UNIQUE(user_id, form_id)
    );
    """
    
    def __init__(self, session_factory):
        """
        :param session_factory: AsyncSession factory из SQLAlchemy
        """
        self._session_factory = session_factory
    
    async def load_state(self, user_id: int, form_id: str) -> Optional[FormState]:
        from sqlalchemy import text
        
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT user_id, form_id, chat_id, current_step_index, 
                           collected_data, started_at, updated_at, 
                           is_completed, is_cancelled, verification_code, pending_email
                    FROM form_states 
                    WHERE user_id = :user_id AND form_id = :form_id
                """),
                {"user_id": user_id, "form_id": form_id}
            )
            row = result.fetchone()
            
            if not row:
                return None
            
            return FormState(
                user_id=row.user_id,
                form_id=row.form_id,
                chat_id=row.chat_id,
                current_step_index=row.current_step_index,
                collected_data=row.collected_data or {},
                started_at=row.started_at.isoformat() if row.started_at else datetime.utcnow().isoformat(),
                updated_at=row.updated_at.isoformat() if row.updated_at else datetime.utcnow().isoformat(),
                is_completed=row.is_completed,
                is_cancelled=row.is_cancelled,
                verification_code=row.verification_code,
                pending_email=row.pending_email
            )
    
    async def save_state(self, state: FormState) -> None:
        from sqlalchemy import text
        
        state.updated_at = datetime.utcnow().isoformat()
        
        async with self._session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO form_states 
                        (user_id, form_id, chat_id, current_step_index, collected_data,
                         started_at, updated_at, is_completed, is_cancelled, 
                         verification_code, pending_email)
                    VALUES 
                        (:user_id, :form_id, :chat_id, :current_step_index, :collected_data,
                         :started_at, :updated_at, :is_completed, :is_cancelled,
                         :verification_code, :pending_email)
                    ON CONFLICT (user_id, form_id) 
                    DO UPDATE SET
                        current_step_index = EXCLUDED.current_step_index,
                        collected_data = EXCLUDED.collected_data,
                        updated_at = EXCLUDED.updated_at,
                        is_completed = EXCLUDED.is_completed,
                        is_cancelled = EXCLUDED.is_cancelled,
                        verification_code = EXCLUDED.verification_code,
                        pending_email = EXCLUDED.pending_email
                """),
                {
                    "user_id": state.user_id,
                    "form_id": state.form_id,
                    "chat_id": state.chat_id,
                    "current_step_index": state.current_step_index,
                    "collected_data": json.dumps(state.collected_data),
                    "started_at": state.started_at,
                    "updated_at": state.updated_at,
                    "is_completed": state.is_completed,
                    "is_cancelled": state.is_cancelled,
                    "verification_code": state.verification_code,
                    "pending_email": state.pending_email
                }
            )
            await session.commit()
    
    async def reset_state(self, user_id: int, form_id: str) -> None:
        from sqlalchemy import text
        
        async with self._session_factory() as session:
            await session.execute(
                text("DELETE FROM form_states WHERE user_id = :user_id AND form_id = :form_id"),
                {"user_id": user_id, "form_id": form_id}
            )
            await session.commit()
    
    async def exists(self, user_id: int, form_id: str) -> bool:
        from sqlalchemy import text
        
        async with self._session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM form_states WHERE user_id = :user_id AND form_id = :form_id"),
                {"user_id": user_id, "form_id": form_id}
            )
            return result.fetchone() is not None


# Глобальное in-memory хранилище (singleton для простоты)
_global_memory_storage = InMemoryFormStateStorage()


def get_memory_storage() -> InMemoryFormStateStorage:
    """Получить глобальное in-memory хранилище"""
    return _global_memory_storage


def get_fsm_storage(fsm_context: FSMContext) -> FSMContextFormStateStorage:
    """Создать хранилище на базе FSMContext"""
    return FSMContextFormStateStorage(fsm_context)
