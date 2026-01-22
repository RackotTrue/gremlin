from main.exception import MyException


class IsNotAdminException(MyException):

    def __init__(self):
        super().__init__("Команда доступна только для администратора!")


class IncorrectSerialNumberException(MyException):
    
    def __init__(self):
        super().__init__("Введен некорректный серийный номер!\n"
                         "Серийный номер устройства должен содержать набор цифр")


class IncorrectDateOfPurchaseException(MyException):

    def __init__(self):
        super().__init__("Введен некорректный формат даты!\n"
                         "Дата должна быть в формет ДД.ММ.ГГГГ")


class IncorrectPeriodDateException(MyException):

    def __init__(self):
        super().__init__("Дата должна быть не раньше _01.01.1900_ и не позже сегодняшней даты!")


class IncorrectNameException(MyException):

    def __init__(self):
        super().__init__("Данные ФИО должны содержать только буквы и возможен дефис!")


class IncorrectPhoneException(MyException):

    def __init__(self):
        super().__init__("Введен некорректный номер телефона!\n"
                         "Номер должен начинаться с +7, без пробелов и спец символов, и содержать 11 цифр")


class IncorrectEmailException(MyException):

    def __init__(self):
        super().__init__("Введен невалидный Email!")


class IncorrectCheckingEmailCodeException(MyException):

    def __init__(self):
        super().__init__("Проверочный код должен содержать только цифры!")


class WrongCheckingEmailCodeException(MyException):

    def __init__(self):
        super().__init__("Неверный код!")


class IncorrectFileFormatException(MyException):

    def __init__(self):
        super().__init__("Введен некорректный формат файла! Необходим файл в формате .pdf")


class IncorrectFileNameException(MyException):

    def __init__(self):
        super().__init__("Введен некорректное имя файла! Название файла должно быть на латинице")


class NotFoundDeviceException(MyException):

    def __init__(self):
        super().__init__("Ваше устройство не было найдено в системе!\n"
                         "Пожалуйста перепроверьте свои данные.")


class DeviceIsRegisteredException(MyException):

    def __init__(self):
        super().__init__("Устройство с таким серийным номером уже было зарегистрировано ранее!")


class NotFoundUserException(MyException):

    def __init__(self):
        super().__init__("Пользователь не был найден в системе!")


class NotFoundGuaranteeException(MyException):

    def __init__(self):
        super().__init__("Гарантийный план не был найден в системе!")


class NotFoundDeviceBySerialNumberException(MyException):

    def __init__(self, serial_number):
        super().__init__(f"Устройство с указанным серийным номером {serial_number} не найдено!\n"
                         "Пожалйста перепроверьте свои данные.")


class NotFoundContactInBitrix24Exception(MyException):

    def __init__(self, phone):
        super().__init__(f"Клиент с номером телефона {phone} не найден в системе Битрикс24")

class DeviceHasStandardGuaranteeTypeException(MyException):

    def __init__(self):
        super().__init__("На данное устройство ранее уже был активирован гарантийный план 'Стандарт'")