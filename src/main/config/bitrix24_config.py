from typing import Final

from main.config.dynaconf_config import config_setting


WEBHOOK: Final = config_setting.BITRIX24.WEBHOOK


# Параметры запроса API
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


# Запросы API
CRM_CONTACT_ADD_BITRIX24_API: Final = "crm.contact.add"
CRM_CONTACT_UPDATE_BITRIX24_API: Final = "crm.contact.update"
CRM_ITEM_LIST_BITRIX24_API: Final = "crm.item.list"
CRM_DEAL_ADD_BITRIX24_API: Final = "crm.deal.add.json"


# Категория сделок для воронки "Гарантия МП"
DEAL_CATEGORY_ID_GUARANTEE_MP: Final = config_setting.BITRIX24.GUARANTEE_MP_CATEGORY_ID


# Пользовательские поля

    # Карточка Сделки
DEAL_FIELD_DEVICE_TYPE: Final = "UF_CRM_1755529008802"             # Поле "Тип устройства (гарантия)"
DEAL_FIELD_DEVICE_PURCHASE_DATE: Final = "UF_CRM_1755529038065"    # Поле "Дата покупки (гарантия)"
DEAL_FIELD_DEVICE_SERIAL_NUMBER: Final = "UF_CRM_1755529067817"    # Поле "Серийный номер (гарантия)"