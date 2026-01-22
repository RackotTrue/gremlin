from typing import Final
from enum import *

GUARANTEE_PERIOD_LENGTH_STANDARD: Final = 24  # 2 года гарантии
GUARANTEE_PERIOD_LENGTH_COMFORT: Final = 0
GUARANTEE_PERIOD_LENGTH_PREMIUM: Final = 0


class GuaranteeTypeEnum(Enum):
    STANDARD = "Стандарт"
    COMFORT = "Комфорт"
    PREMIUM = "Премиум"


class GuaranteeInformationEnum(Enum):
    STANDARD = ("*Стандарт*\n"
                "  ✔ 12 месяцев гарантии\n"
                "  ✔ Стандартные сроки обслуживания\n"
                "  ✔ Бесплатная доставка в сервис от пункта выдачи транспортной компании и обратно\n"
                "_Стоимость ₽_: ")
    COMFORT = ("*Комфорт*\n"
              "  ✔ 18 месяцев гарантии\n"
              "  ✔ Срок обслуживания до 10 дней\n"
              "  ✔ Бесплатная доставка в сервис от двери вашего дома и обратно\n"
              "_Стоимость ₽_: ")
    PREMIUM = ("*Премиум*\n"
               "  ✔ 30 месяцев гарантии\n"
               "  ✔ Срок обслуживания до 3 дней\n"
               "  ✔ Бесплатная доставка в сервис от двери вашего дома и обратно\n"
               "_Стоимость ₽_: ")
