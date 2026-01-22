from enum import *


class CheckUserDataButton(Enum):

    APPROVE = "Верно ✅"
    UPDATE = "Редактировать 🖍"


class UpdateUserDataButton(Enum):

    NAME = "Имя 📰"
    SURNAME = "Фамилия 📰"
    PHONE = "Телефон ☎"
    EMAIL = "Email 📫"
    SERIAL_NUMBER = "Серийный номер устройства ®"
    PURCHASE_DATE = "Дата покупки устройства 📆"
    CITY = "Город 🏙"
    ORDER_SOURCE = "Источник заказа 🛒"


class OrderSourceEnum(Enum):
    """Источники заказа"""
    OZON = "Ozon"
    WILDBERRIES = "Wildberries"
    YANDEX_MARKET = "Яндекс Маркет"
    AVITO = "Avito"
    RETAIL = "Сетка Гармошка"


class ConsentButton(Enum):
    """Кнопки согласия"""
    AGREE = "Согласен ✅"