from main.config.bitrix24_config import *
from main.config.log_config import logger
from main.dto.guarantee_request_dto import GuaranteeCreateBitrix24RequestDTO
from main.exception.exception import NotFoundContactInBitrix24Exception
from main.model.user_base import UserBase
from main.utils import send_request
from main.config.dynaconf_config import config_setting


async def create_contact(user: UserBase):
    """
    Метод создания контакта в Битрикс24

    :param user: Данные клиента
    :return: id клинета в в системе Битрикс24
    """

    try:

        url = str(WEBHOOK) + CRM_CONTACT_ADD_BITRIX24_API

        data = {
            "fields": {
                "NAME": user.name,
                "LAST_NAME": user.surname,
                "TYPE_ID": "CLIENT",
                "PHONE": [
                    {
                        "VALUE": user.phone,
                        "VALUE_TYPE": "WORK",
                    }
                ],
                "EMAIL": [
                    {
                        "VALUE": user.email,
                        "VALUE_TYPE": "WORK",
                    }
                ],
                # Город клиента (стандартное поле контакта)
                "ADDRESS_CITY": user.city or "",
            }
        }

        request = send_request(type="POST",
                               url=url,
                               json=data,
                               headers=headers).json()

        bitrix_contact_id = request['result']

        logger.info(f"Создание контакта прошло успешно: {bitrix_contact_id}", extra={"service": "bitrix24"})

        return bitrix_contact_id

    except Exception as e:
        logger.error(f"Ошибка при создании контакта в системе Битрикс24: {e}", extra={"service": "bitrix24"})


async def update_contact(bitrix_contact_id: int, user: UserBase):
    """
    Метод обновляет контакт в Битрикс 24

    :param bitrix_contact_id: id клинета в в системе Битрикс24
    :param user: данные пользователя
    """
    try:

        url = str(WEBHOOK) + CRM_CONTACT_UPDATE_BITRIX24_API

        data = {
            "id": bitrix_contact_id,
            "fields": {
                "NAME": user.name,
                "LAST_NAME": user.surname,
                "TYPE_ID": "CLIENT",
                "PHONE": [
                    {
                        "VALUE": user.phone,
                        "VALUE_TYPE": "WORK",
                    }
                ],
                "EMAIL": [
                    {
                        "VALUE": user.email,
                        "VALUE_TYPE": "WORK",
                    }
                ],
                "ADDRESS_CITY": user.city or "",
            },
        }

        request = send_request(type="POST",
                               url=url,
                               json=data,
                               headers=headers).json()

        logger.info(f"Обновление контакта с id {bitrix_contact_id} прошло успешно", extra={"service": "bitrix24"})

    except Exception as e:
        logger.error(f"Ошибка при обновлении контакта с id {bitrix_contact_id} в системе Битрикс24: {e}", extra={"service": "bitrix24"})


async def get_contact_by_phone(phone):
    """
    Поиск клиента в системе Битрикс24 по номеру телефона

    :param phone: Номер телефона
    :return: id клинета в в системе Битрикс24
    """

    try:
        url = str(WEBHOOK) + CRM_ITEM_LIST_BITRIX24_API

        data = {
            "entityTypeId": 3,
            "filter": {
                "phone": phone
            }
        }

        request = send_request(type="POST",
                               url=url,
                               json=data,
                               headers=headers).json()

        if len(request["result"]["items"]) == 0:
            raise NotFoundContactInBitrix24Exception(phone)
        else:
            bitrix_contact_id = request["result"]["items"][0]["id"]

            logger.info(f"Найден контакт в системе Битрикс24: {bitrix_contact_id}", extra={"service": "bitrix24"})

            return bitrix_contact_id


    except NotFoundContactInBitrix24Exception:
        raise
    except Exception as e:
        logger.error(f"Ошибка при поиске контакта в системе Битрикс24: {e}", extra={"service": "bitrix24"})


async def create_guarantee_deal(guarantee_dto: GuaranteeCreateBitrix24RequestDTO, contact_id):
    """
    Метод создает Сделку в системе Битрикс24

    :param guarantee_dto: ДТО гарантийного плана для создания в Битрикс24
    :param contact_id:  для создания в Битрикс24
    :return: id сделки в системе Битрикс24
    """

    try:

        url = str(WEBHOOK) + "crm.deal.add.json"

        user = guarantee_dto.user
        device = guarantee_dto.device

        purchase_date_str = (
            device.purchase_date.strftime("%d.%m.%Y") if device.purchase_date else "не указана"
        )

        comments = (
            f"Оформление гарантийного плана типа {guarantee_dto.type} на сумму {guarantee_dto.price}. "
            f"Устройство: модель {device.model or 'не указана'}, "
            f"серийный номер {device.serial_number or 'не указан'}, "
            f"дата покупки {purchase_date_str}.\n"
            f"Клиент: {user.surname or ''} {user.name or ''}\n"
            f"Телефон: {user.phone or 'не указан'}, email: {user.email or 'не указан'}\n"
            f"Город: {user.city or 'не указан'}\n"
            f"Маркетплейс / источник заказа: {user.order_source or 'не указан'}\n"
            f"Согласие на ПДн: {'да' if user.pd_consent else 'нет'}, "
            f"согласие на маркетинг: {'да' if user.marketing_consent else 'нет'}\n"
            f"ID заказа: не указано, SKU: не указано, размер: не указан, сезонность: не указана, "
            f"бренд/модель: {device.model or 'не указана'}"
        )

        data = {
            "fields": {
                "TITLE": f"Покупка гарантийного плана типа {guarantee_dto.type}. Бот",
                # Воронка "Гарантия МП"
                "CATEGORY_ID": DEAL_CATEGORY_ID_GUARANTEE_MP,
                "CURRENCY_ID": "RUB",
                "OPPORTUNITY": guarantee_dto.price,
                "CONTACT_IDS": [contact_id],
                "COMMENTS": comments,
                # Пользовательские поля сделки
                DEAL_FIELD_DEVICE_TYPE: device.model,
                DEAL_FIELD_DEVICE_PURCHASE_DATE: (
                    device.purchase_date.strftime("%d.%m.%Y") if device.purchase_date else ""
                ),
                DEAL_FIELD_DEVICE_SERIAL_NUMBER: device.serial_number,
            },
            "params": {
                "REGISTER_SONET_EVENT": "N",
            },
        }

        request = send_request(type="POST",
                               url=url,
                               json=data,
                               headers=headers).json()

        deal_id = request['result']

        logger.info(f"Успешное создание Сделки в системе Битрикс24: {deal_id}", extra={"service": "bitrix24"})

        return deal_id

    except Exception as e:

        logger.error(f"Ошибка при создании Сделки в системе Битрикс24: {e}", extra={"service": "bitrix24"})
