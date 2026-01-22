from aiogram.filters import Command
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import *
from pyasn1_modules.rfc5639 import ecStdCurvesAndGeneration

from main.config.dynaconf_config import security_setting
from main.keyboard.administration_keyboard import approve_delete_device_keyboard
from main.middleware.middleware import ChatActionMiddleware
from main.model.device_base import DeviceBase
from main.service.handler.administration_handler_service import delete_guarantees_and_device_by_serial_number
from main.state.administration_state import DeleteDeviceState
from main.utils import *


###### Хендлер для работы с командами администратора
####
##


router = Router()
router.message.middleware(ChatActionMiddleware())


@router.message(Command('stop'))
async def stop(message: Message):
    """
    Метод завершает работу бота и выключает его

    :param message: Сообщение от пользоваетля
    """

    try:
        await is_admin(message.chat.id)
        await send_message_from_msg(message=message,
                                    text="Бот завершил свою работу")
        await bot.close()
        exit()

    except IsNotAdminException as e:
        await send_message_from_msg(message=message, text=str(e))


@router.message(Command('get_admin_ids'))
async def get_admin_ids(message: Message):
    """
    Метод возвращает id всех администраторов

    :param message: Сообщение пользователя
    """

    try:
        await is_admin(message.chat.id)
        await send_message_from_msg(message=message,
                                    text=f"Id текущих администраторов: {security_setting.IDS}")

    except IsNotAdminException as e:
        await send_message_from_msg(message=message, text=str(e))


@router.message(Command("device/delete"))
async def delete_device_and_guarantee(message: Message, state: FSMContext):
    """
    Метод инициализирует удаление устройства и запрашивает серийный номер

    :param message: Сообщение пользователя
    :param state: Состояние
    """

    try:
        await is_admin(message.chat.id)
        await send_message_from_msg(message=message,
                                    text="Введите серийный номер устройства, который хотите удалить",
                                    keyboard=cancel_action_keyboard)

        await  state.set_state(DeleteDeviceState.serial_number)
    except IsNotAdminException as e:
        await send_message_from_msg(message=message, text=str(e))


@router.message(DeleteDeviceState.serial_number)
async def set_serial_number_and_prepare_to_approve(message: Message, state: FSMContext):
    """
    Метод принимает серийный номер и запрашивает подтверждение

    :param message: Сообщение пользователя
    :param state: Состояние
    """

    serial_number = message.text
    await state.update_data(serial_number=serial_number)
    await delete_previous_message_and_send_new_from_msg(message=message,
                                                        text=f"Вы уверены, что хотите удалить устройство с серийным номером {serial_number} и все его гарантийные планы?",
                                                        keyboard=approve_delete_device_keyboard)


@router.callback_query(F.data == "delete_device_approve")
async def delete_device_and_guarantees(call: CallbackQuery, state: FSMContext):
    """
    Метод удаляет устройство и все его гарантийные планы

    :param call: Вызов кнопки
    :param state: Состояние
    """
    try:
        state_dict = await state.get_data()
        serial_number = state_dict["serial_number"]


        await delete_guarantees_and_device_by_serial_number(serial_number)

        await delete_previous_message_and_send_new_from_call(call=call,
                                                            text=f"Устройство с серийным номером {serial_number} и все его гарантийные планы успешно удалены")

        await state.clear()

    except NotFoundDeviceException as e:
        await send_exception_and_request_data_again_from_call(call=call,
                                                             exception_text=e)
        await state.set_state(DeleteDeviceState.serial_number)

    except Exception:
        logger.error(f"Произошла ошибка", exc_info=True, extra={"service": "administration_handler"})
        await send_message_from_call(call=call,
                                    text=f"Произошла непредвиденная ошибка, пожалуйста обратитесь к администратору!")










