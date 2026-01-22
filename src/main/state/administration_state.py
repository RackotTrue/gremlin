from aiogram.fsm.state import StatesGroup, State


class DeleteDeviceState(StatesGroup):
    serial_number = State()


class BroadcastTextState(StatesGroup):
    """Состояния для рассылки текста"""
    text = State()
    confirm = State()


class BroadcastPhotoState(StatesGroup):
    """Состояния для рассылки фото"""
    photo = State()
    text = State()
    confirm = State()


class BroadcastVideoState(StatesGroup):
    """Состояния для рассылки видео"""
    video = State()
    text = State()
    confirm = State()