from typing import Final

from main.config.dynaconf_config import config_setting

EMAIL_SENDER_ADDRESS: Final = config_setting.MAIL.ADDRESS
EMAIL_PASSWORD: Final = config_setting.MAIL.PASSWORD
SMTP_SERVER: Final = config_setting.MAIL.SMTP_SERVER
SMTP_PORT: Final = int(config_setting.MAIL.SMTP_PORT)
# Получаем use_tls с дефолтом в зависимости от порта
SMTP_USE_TLS: Final = getattr(config_setting.MAIL, 'USE_TLS', SMTP_PORT == 465)  # По умолчанию true для 465
# Получаем timeout с дефолтом 30 секунд
SMTP_TIMEOUT: Final = int(getattr(config_setting.MAIL, 'TIMEOUT', 30))  # По умолчанию 30 секунд