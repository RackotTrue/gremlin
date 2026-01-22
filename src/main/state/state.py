from aiogram.fsm.state import StatesGroup, State


class RegistrationAndActivateGuaranteeState(StatesGroup):
    begin_registration = State()
    # Согласия (в начале)
    pd_consent = State()  # Согласие на обработку ПДн
    marketing_consent = State()  # Согласие на маркетинг
    # Данные пользователя
    set_surname = State()
    set_name = State()
    set_phone = State()
    set_email = State()
    set_checking_code = State()
    set_city = State()  # Город/регион
    set_order_source = State()  # Источник заказа
    # Данные устройства
    set_serial_number = State()
    set_purchase_date = State()


class ActivateGuaranteeState(StatesGroup):
    set_serial_number = State()
    set_purchase_date = State()


class UpdateUserAndDeviceDataState(StatesGroup):
    name = State()
    surname = State()
    phone = State()
    email = State()
    serial_number = State()
    purchase_date = State()
    device_id = State()
    checking_code = State()


class UpdateUserDataState(StatesGroup):
    name = State()
    surname = State()
    phone = State()
    email = State()
    checking_code = State()


class DeviceState(StatesGroup):
    device_id = State()
    guarantee_id = State()

