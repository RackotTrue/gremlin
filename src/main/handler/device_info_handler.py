from aiogram import Router
from aiogram.types import Message, CallbackQuery

from main.dto.device_info_response_dto import DeviceInfoResponseRTO
from main.dto.device_response_dto import DeviceResponseDTO
from main.exception.exception import NotFoundDeviceException
from main.keyboard.device_info_keyboard import get_device_keyboard, ChoiceDeviceCall
from main.middleware.middleware import ChatActionMiddleware
from main.model.user_base import UserBase
from main.service.model.device_service import DeviceService
from main.service.model.guarantee_service import GuaranteeService
from main.service.model.user_service import UserService
from main.utils import send_message_from_msg, send_message_from_call, delete_previous_message_and_send_new_from_call

###
###### Хендлер для работы с информацией по устройствам пользователя
####
##


router = Router()
router.message.middleware(ChatActionMiddleware())

user_service = UserService()
guarantee_service = GuaranteeService()
device_service = DeviceService()


async def devices_info(message: Message):
    """
    Метод предлагает выбрать устройство пользователя

    :param message: Сообщение пользователя
    """

    try:
        user: UserBase = await user_service.create_user(chat_id=message.chat.id,
                                                        username=message.from_user.username,
                                                        full_name=message.from_user.full_name)

        devices = await device_service.get_devices_by_user_id(user.chat_id)

        await send_message_from_msg(message=message,
                                    text="Выберите устройство",
                                    keyboard=await get_device_keyboard(devices))

    except NotFoundDeviceException:
        await send_message_from_msg(message=message,
                                    text="Данных об устройствах не обнаружено. Зарегистрируйте устройство через команду 'Активация гарантии' (/guarantee)")


@router.callback_query(ChoiceDeviceCall.filter())
async def get_device_info(call: CallbackQuery, callback_data: ChoiceDeviceCall):
    """
    Метод возвращает информацию по устройству и последнему гарантийному плану

    :param call: Вызов кнопки
    :param callback_data: Данные, переданные в кнопке
    """

    device_id = callback_data.device_id

    device = await device_service.get_device_with_guarantee(device_id)
    device_info_dto = DeviceInfoResponseRTO(device)

    await delete_previous_message_and_send_new_from_call(call=call,
                                                         text=await device_info_dto.get_device_info_text())
