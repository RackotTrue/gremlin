from enum import Enum


class ProductEnum(Enum):
    """
    Каталог товаров, которые может выбрать покупатель на этапе активации гарантии.

    Кортеж полей:
      0. id — технический идентификатор (совпадает с id героя в heroes.yml)
      1. display_name — как показываем на кнопке и в интерфейсе
      2. image_filename — имя файла в src/resources/products/
    """

    TENT_HOUSE = ("tent_house", "Палатка детская «Домик» 🏠", "1 - 312092267.png")
    TENT_3IN1 = ("tent_3in1", "Палатка детская «3 в 1» ⛺", "2 - 58452308.png")
    TENT_SHATER = ("tent_shater", "Палатка детская «Шатёр» 🏕", "3 - 424774838.png")
    CONSTRUCTOR = ("constructor", "Конструктор 🧱", "4 - 336435693.png")
    BOX_TRAINER = ("box_trainer", "Тренажёр для бокса 🥊", "5 - 758048932.png")
    NIGHT_LIGHT = ("night_light", "Ночник 💡", "6 - 492884902 .png")
    TOY_CAR = ("toy_car", "Машинка 🚗", "7 - 349664142 .png")

    def __init__(self, product_id: str, display_name: str, image_filename: str):
        self.product_id = product_id
        self.display_name = display_name
        self.image_filename = image_filename

    @classmethod
    def from_id(cls, product_id: str) -> "ProductEnum | None":
        """Найти товар по его техническому id. Возвращает None, если не найден."""
        for product in cls:
            if product.product_id == product_id:
                return product
        return None
