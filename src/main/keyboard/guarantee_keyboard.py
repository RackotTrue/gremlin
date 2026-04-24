from sys import prefix

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from main.enum.guarantee_enum import GuaranteeTypeEnum
from main.enum.main_menu_enum import MainMenuButtonEnum
from main.enum.product_enum import ProductEnum
from main.enum.user_enum import CheckUserDataButton, UpdateUserDataButton, OrderSourceEnum, ConsentButton
from aiogram.filters.callback_data import CallbackData


# Клавиатура согласия на обработку ПДн
pd_consent_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=ConsentButton.AGREE.value, callback_data="pd_consent_agree")]
])

# Клавиатура согласия на маркетинг
marketing_consent_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=ConsentButton.AGREE.value, callback_data="marketing_consent_agree")]
])

# Клавиатура выбора источника заказа
order_source_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=OrderSourceEnum.OZON.value, callback_data="order_source_ozon")],
    [InlineKeyboardButton(text=OrderSourceEnum.WILDBERRIES.value, callback_data="order_source_wb")],
    [InlineKeyboardButton(text=OrderSourceEnum.YANDEX_MARKET.value, callback_data="order_source_ym")],
    [InlineKeyboardButton(text=OrderSourceEnum.AVITO.value, callback_data="order_source_avito")],
    [InlineKeyboardButton(text=OrderSourceEnum.RETAIL.value, callback_data="order_source_retail")]
])


# Клавиатура выбора купленного товара
# Префикс callback_data — "product_", значение — product_id из ProductEnum
product_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=product.display_name, callback_data=f"product_{product.product_id}")]
    for product in ProductEnum
])


def get_video_greeting_launch_keyboard(product_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой запуска видео-открытки для выбранного товара.

    :param product_id: id товара (и одновременно id героя в heroes.yml)
    :return: Клавиатура с двумя кнопками: «Оживить героя» и «Позже»
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎬 Оживить героя для ребёнка",
            callback_data=f"start_video_greeting_for:{product_id}",
        )],
        [InlineKeyboardButton(
            text="⏰ Позже",
            callback_data="video_greeting_later",
        )],
    ])


class UserDataApproveCall(CallbackData, prefix="user_and_device_data_approve"):
    device_id:int

class UserDataUpdateCall(CallbackData, prefix="user_and_device_data_update"):
    device_id:int

class UpdateUserCall(CallbackData, prefix="update_user"):
    device_id:int
    param: str

class UpgradeStandardGuaranteeCall(CallbackData, prefix="upgrade_standard_guarantee_type"):
    device_id:int
    guarantee_standard_price: int
    # guarantee_comfort_price: int
    # guarantee_premium_price: int

class GuaranteeTypeCall(CallbackData, prefix="guarantee_type"):
    device_id:int
    guarantee_standard_price: int
    # guarantee_comfort_price: int
    # guarantee_premium_price: int
    type: str


# Клавиатура подтверждения данных пользователя
check_user_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=CheckUserDataButton.APPROVE.value,
                          callback_data="user_data_approve")],
    [InlineKeyboardButton(text=CheckUserDataButton.UPDATE.value,
                          callback_data="user_data_update")]
])


# Клавиатура редактирования данных пользователя
update_user_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=UpdateUserDataButton.NAME.value, callback_data="update_user_data_name"),
         InlineKeyboardButton(text=UpdateUserDataButton.SURNAME.value, callback_data="update_user_data_surname")],
        [InlineKeyboardButton(text=UpdateUserDataButton.PHONE.value, callback_data="update_user_data_phone"),
         InlineKeyboardButton(text=UpdateUserDataButton.EMAIL.value, callback_data="update_user_data_email")],
    ])


async def get_check_user_and_device_data_keyboard(device_id: int) -> InlineKeyboardMarkup:
    """
    Метод возвращает клавиатуру для проверки правильности введенных данных пользователя
    с переданным в ней id устройства

    :param device_id: id устройства
    :return: Клавиатура
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=CheckUserDataButton.APPROVE.value, callback_data=UserDataApproveCall(device_id=device_id).pack())],
        [InlineKeyboardButton(text=CheckUserDataButton.UPDATE.value, callback_data=UserDataUpdateCall(device_id=device_id).pack())]
    ])

    return keyboard


async def get_guarantee_type_keyboard(device_id: int,
                                      guarantee_standard_price: int
                                      # guarantee_comfort_price: int,
                                      # guarantee_premium_price: int
                                      ) -> InlineKeyboardMarkup:
    """
    Метод возвращает клавиатуру для выбора гарантийного плана
    с переданным в ней id устройства и типом гарантии

    :param device_id: id устройства
    :param guarantee_standard_price: стоимость гарантийного плана "Стандарт" для устройства
    :param guarantee_comfort_price: стоимость гарантийного плана "Комфорт" для устройства
    :param guarantee_premium_price: стоимость гарантийного плана "Премиум" для устройства
    :return: Клавиатура
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{GuaranteeTypeEnum.STANDARD.value} {guarantee_standard_price} ₽", callback_data=GuaranteeTypeCall(device_id=device_id,
                                                                                                                                       type="standard",
                                                                                                                                       guarantee_standard_price=guarantee_standard_price
                                                                                                                                       ).pack())]

        # [InlineKeyboardButton(text=f"{GuaranteeTypeEnum.STANDARD.value} {guarantee_standard_price} ₽", callback_data=UpgradeStandardGuaranteeCall(device_id=device_id,
        #                                                                                                                                           guarantee_standard_price=guarantee_standard_price
        #                                                                                                                                           guarantee_comfort_price=guarantee_comfort_price,
        #                                                                                                                                           guarantee_premium_price=guarantee_premium_price
        #                                                                                                                                           ).pack()),
        #  InlineKeyboardButton(text=f"{GuaranteeTypeEnum.COMFORT.value} {guarantee_comfort_price} ₽", callback_data=GuaranteeTypeCall(device_id=device_id,
        #                                                                                                                              type="comfort",
        #                                                                                                                              guarantee_standard_price=guarantee_standard_price,
        #                                                                                                                              guarantee_comfort_price=guarantee_comfort_price,
        #                                                                                                                              guarantee_premium_price=guarantee_premium_price
        #                                                                                                                              ).pack())],
        # [InlineKeyboardButton(text=f"{GuaranteeTypeEnum.PREMIUM.value} {guarantee_premium_price} ₽", callback_data=GuaranteeTypeCall(device_id=device_id,
        #                                                                                                                              type="premium",
        #                                                                                                                              guarantee_standard_price=guarantee_standard_price,
        #                                                                                                                              guarantee_comfort_price=guarantee_comfort_price,
        #                                                                                                                              guarantee_premium_price=guarantee_premium_price
        #                                                                                                                              ).pack())]
    ])

    return keyboard


async def get_upgrade_guarantee_type_keyboard(device_id: int,
                                              guarantee_standard_price: int,
                                              guarantee_comfort_price: int,
                                              guarantee_premium_price: int
                                              ) -> InlineKeyboardMarkup:
    """
    Метод возвращает клавиатуру для улучшения гарантийного плана при начальном выборе - "Стандарт"
    с переданным в ней id устройства и типом гарантии

    :param device_id: id устройства
    param guarantee_standard_price: стоимость гарантийного плана "Стандарт" для устройства
    :param guarantee_comfort_price: стоимость гарантийного плана "Комфорт" для устройства
    :param guarantee_premium_price: стоимость гарантийного плана "Премиум" для устройства
    :return: Клавиатура
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=GuaranteeTypeEnum.COMFORT.value, callback_data=GuaranteeTypeCall(device_id=device_id,
                                                                                                    type="comfort",
                                                                                                    guarantee_standard_price=guarantee_standard_price,
                                                                                                    guarantee_comfort_price=guarantee_comfort_price,
                                                                                                    guarantee_premium_price=guarantee_premium_price
                                                                                                    ).pack()),
         InlineKeyboardButton(text=GuaranteeTypeEnum.PREMIUM.value, callback_data=GuaranteeTypeCall(device_id=device_id,
                                                                                                    type="premium",
                                                                                                    guarantee_standard_price=guarantee_standard_price,
                                                                                                    guarantee_comfort_price=guarantee_comfort_price,
                                                                                                    guarantee_premium_price=guarantee_premium_price
                                                                                                    ).pack())],
        [InlineKeyboardButton(text=MainMenuButtonEnum.MAIN_ACTION_REFUSE.value, callback_data=GuaranteeTypeCall(device_id=device_id,
                                                                                                                type="standard",
                                                                                                                guarantee_standard_price=guarantee_standard_price,
                                                                                                                guarantee_comfort_price=guarantee_comfort_price,
                                                                                                                guarantee_premium_price=guarantee_premium_price
                                                                                                                ).pack())]
    ])

    return keyboard


async def get_update_user_keyboard(device_id: int) -> InlineKeyboardMarkup:
    """
    Метод возвращает клавиатуру для редактирования данных пользователя
    с переданным в ней id устройства и типом изменяемого параметра

    :param device_id: id устройства
    :return: Клавиатура
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=UpdateUserDataButton.NAME.value, callback_data=UpdateUserCall(device_id=device_id, param="name").pack()),
         InlineKeyboardButton(text=UpdateUserDataButton.SURNAME.value, callback_data=UpdateUserCall(device_id=device_id, param="surname").pack())],
        [InlineKeyboardButton(text=UpdateUserDataButton.PHONE.value, callback_data=UpdateUserCall(device_id=device_id, param="phone").pack()),
         InlineKeyboardButton(text=UpdateUserDataButton.EMAIL.value, callback_data=UpdateUserCall(device_id=device_id, param="email").pack())]
    ])

    return keyboard
