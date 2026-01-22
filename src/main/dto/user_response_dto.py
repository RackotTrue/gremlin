from main.model.user_base import UserBase


class UserResponseDTO():

    name: str
    surname: str
    phone: str
    email: str

    def __init__(self, user: UserBase):

        self.name = user.name
        self.surname = user.surname
        self.phone = user.phone
        self.email = user.email


    async def get_user_text(self):
        """
        Метод возвращает текстовую информацию по пользователю

        :return: текстовая информация
        """
        text = (f"🔸 Фамилия и имя: _{self.surname}_ _{self.name}_\n"
                f"🔸 Номер телефона: _{self.phone}_\n"
                f"🔸 Email: _{self.email}_\n")

        return text