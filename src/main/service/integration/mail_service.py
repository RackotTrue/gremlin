import random
import ssl
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.utils import formataddr

from main.config.log_config import logger
from main.config.mail_config import (
    EMAIL_SENDER_ADDRESS,
    EMAIL_PASSWORD,
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_TIMEOUT
)


def _send_mail_sync(msg_object: MIMEText):
    """
    Синхронная функция отправки email через стандартную библиотеку smtplib
    
    :param msg_object: MIME-объект письма
    """
    server = None
    try:
        # Создаем SSL контекст с более мягкими настройками для nic.ru
        context = ssl.create_default_context()
        # Разрешаем менее строгие сертификаты (для некоторых SMTP серверов)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        logger.info(f"Попытка подключения к {SMTP_SERVER}:{SMTP_PORT}", extra={"service": "mail"})
        
        if SMTP_PORT == 465:
            # Порт 465 - используем SSL при подключении
            server = smtplib.SMTP_SSL(
                SMTP_SERVER,
                SMTP_PORT,
                timeout=SMTP_TIMEOUT,
                context=context
            )
            logger.info("Подключение установлено (SSL, порт 465)", extra={"service": "mail"})
        elif SMTP_PORT == 587:
            # Порт 587 - используем STARTTLS
            server = smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT,
                timeout=SMTP_TIMEOUT
            )
            logger.info("Подключение установлено, запуск STARTTLS", extra={"service": "mail"})
            server.starttls(context=context)
            logger.info("STARTTLS успешно", extra={"service": "mail"})
        else:
            # Другие порты - обычное подключение
            server = smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT,
                timeout=SMTP_TIMEOUT
            )
            logger.info(f"Подключение установлено (порт {SMTP_PORT})", extra={"service": "mail"})
        
        # Авторизация
        logger.info(f"Попытка авторизации как {EMAIL_SENDER_ADDRESS}", extra={"service": "mail"})
        server.login(EMAIL_SENDER_ADDRESS, EMAIL_PASSWORD)
        logger.info("Авторизация успешна", extra={"service": "mail"})
        
        # Отправка письма
        logger.info(f"Отправка письма на {msg_object['To']}", extra={"service": "mail"})
        server.send_message(msg_object)
        logger.info("Письмо отправлено успешно", extra={"service": "mail"})
        
        # Закрытие соединения
        server.quit()
        logger.info("Письмо успешно отправлено через SMTP", extra={"service": "mail"})
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Ошибка аутентификации SMTP: {e}", extra={"service": "mail"})
        if server:
            try:
                server.quit()
            except:
                pass
        raise Exception(f"Ошибка аутентификации: проверьте логин и пароль. {str(e)}")
    except (smtplib.SMTPConnectError, TimeoutError, ConnectionError, OSError) as e:
        logger.error(f"Ошибка подключения к SMTP серверу: {e}", extra={"service": "mail"})
        if server:
            try:
                server.quit()
            except:
                pass
        raise Exception(f"Не удалось подключиться к почтовому серверу {SMTP_SERVER}:{SMTP_PORT}. Возможно, порт заблокирован или сервер недоступен. {str(e)}")
    except smtplib.SMTPException as e:
        logger.error(f"Ошибка SMTP: {e}", extra={"service": "mail"})
        if server:
            try:
                server.quit()
            except:
                pass
        raise Exception(f"Ошибка при отправке письма: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке письма: {e}", extra={"service": "mail"})
        if server:
            try:
                server.quit()
            except:
                pass
        raise Exception(f"Ошибка при отправке письма: {str(e)}")


async def __send_mail(msg_object: MIMEText):
    """
    Асинхронная обертка для отправки электронного письма
    
    :param msg_object: MIME-объект письма
    """
    try:
        # Запускаем синхронную функцию в отдельном потоке
        await asyncio.to_thread(_send_mail_sync, msg_object)
        logger.debug("Письмо успешно отправлено", extra={"service": "mail"})
    except Exception as e:
        logger.error(f"Ошибка при отправке электронного письма: {e}", extra={"service": "mail"})
        raise


# Верификация email включена
# Примечание: Если SMTP недоступен, будет использоваться заглушка с кодом 0000
EMAIL_VERIFICATION_ENABLED = True
# Автоматически использовать заглушку при ошибках подключения
USE_STUB_ON_CONNECTION_ERROR = True


async def send_checking_mail(email):
    """
    Метод отправляет электронное письмо для проверки mail адреса с проверочным кодом

    :param email: Электронный адрес
    :return: Проверочный код
    """

    # ЗАГЛУШКА: Если верификация отключена, возвращаем код 0000
    if not EMAIL_VERIFICATION_ENABLED:
        checking_code = 0
        logger.info(f"[ЗАГЛУШКА] Email {email} принят. Используйте код: 0000", extra={"service": "mail"})
        return checking_code

    try:
        # Генерация рандомного проверочного кода из 4 цифр
        checking_code = random.randint(1000, 9999)

        # Содержание письма
        subject = "ТОП ШИНА 24. Проверка Email"
        body = ("Здравствуйте! Пожалуйста, подтвердите ваш email.\n\n"
                f"Ваш проверочный код: {checking_code}\n\n"
                f"С уважением, команда ТОП ШИНА 24")

        # Создание MIME-объекта письма
        msg_object = MIMEText(body, 'plain', 'utf-8')
        msg_object["Subject"] = subject
        msg_object["From"] = formataddr(("ТОП ШИНА 24", EMAIL_SENDER_ADDRESS))
        msg_object["To"] = email

        # Отправка письма
        await __send_mail(msg_object)

        logger.info(f"Письмо с проверочным кодом ({checking_code}) успешно отправлено на {email}", extra={"service": "mail"})

        return checking_code
        
    except Exception as e:
        error_str = str(e).lower()
        # Проверяем, является ли ошибка ошибкой подключения
        is_connection_error = any(keyword in error_str for keyword in [
            'timeout', 'timed out', 'connection', 'connect', 'не удалось подключиться'
        ])
        
        if USE_STUB_ON_CONNECTION_ERROR and is_connection_error:
            # Если это ошибка подключения и включен fallback на заглушку
            checking_code = 0
            logger.warning(
                f"[FALLBACK НА ЗАГЛУШКУ] Не удалось отправить письмо на {email} из-за ошибки подключения: {e}. "
                f"Используется код 0000", 
                extra={"service": "mail"}
            )
            return checking_code
        else:
            # Для других ошибок пробрасываем исключение
            logger.error(f"Ошибка при отправке электронного письма с проверочным кодом: {e}", extra={"service": "mail"})
            raise Exception(f"Не удалось отправить письмо с кодом подтверждения. Проверьте настройки SMTP или обратитесь к администратору. Ошибка: {str(e)}")
