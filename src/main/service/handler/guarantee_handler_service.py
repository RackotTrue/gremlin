from main.dto.device_response_dto import DeviceResponseDTO
from main.dto.user_response_dto import UserResponseDTO
from main.enum.guarantee_enum import GuaranteeInformationEnum
from main.keyboard.guarantee_keyboard import get_check_user_and_device_data_keyboard, check_user_data_keyboard, \
    get_guarantee_type_keyboard
from main.model.device_base import DeviceBase
from main.model.user_base import UserBase
from main.service.model.device_service import DeviceService
from main.utils import *


device_service = DeviceService()

# Цены на гарантию по умолчанию (Google Sheets отключен)
DEFAULT_GUARANTEE_STANDARD_PRICE = 0
DEFAULT_GUARANTEE_COMFORT_PRICE = 0
DEFAULT_GUARANTEE_PREMIUM_PRICE = 0


async def choice_guarantee_type_handler_service(event, device_id: int):
    """
    Метод предлагает выбрать гарантийный план

    :param event: Событие (CallbackQuery/Message)
    :param device_id: id устройства
    """

    # Цены на гарантию (Google Sheets отключен, используем значения по умолчанию)
    guarantee_standard_price = DEFAULT_GUARANTEE_STANDARD_PRICE
    guarantee_comfort_price = DEFAULT_GUARANTEE_COMFORT_PRICE
    guarantee_premium_price = DEFAULT_GUARANTEE_PREMIUM_PRICE

    text = ("Выберите гарантийный план:\n\n"
            f"1) {GuaranteeInformationEnum.STANDARD.value}\n\n"
            )

    keyboard = await get_guarantee_type_keyboard(device_id=device_id,
                                                 guarantee_standard_price=guarantee_standard_price)

    if isinstance(event, CallbackQuery):
        await delete_previous_message_and_send_new_from_call(call=event, text=text, keyboard=keyboard)

    elif isinstance(event, Message):
        await delete_previous_message_and_send_new_from_msg(message=event, text=text, keyboard=keyboard)


async def send_check_user_and_device_data_message(message: Message, user: UserBase, device: DeviceBase):
    """
    Метод отправляет сообщение с просьбой проверки данных пользователя и устройства

    :param message: Сообщение от пользователя
    :param user: Пользователь
    :param device: Устройство
    """

    user_dto = UserResponseDTO(user)
    device_dto = DeviceResponseDTO()
    await device_dto.from_device_base(device)

    await send_message_from_msg(message=message,
                                text="Проверьте, пожалуйста, ваши данные!\n\n" +
                                     await user_dto.get_user_text() +
                                     await device_dto.get_device_text(),
                                keyboard=await get_check_user_and_device_data_keyboard(device_id=device.id))


async def send_check_user_data_message(message: Message, user: UserBase):
    """
    Метод отправляет сообщение с просьбой проверки данных пользователя

    :param message: Сообщение от пользователя
    :param user: Пользователь
    """

    user_dto = UserResponseDTO(user)

    await send_message_from_msg(message=message,
                                text="Использовать текущие данные?\n\n" +
                                     await user_dto.get_user_text(),
                                keyboard=check_user_data_keyboard)