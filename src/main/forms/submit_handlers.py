"""
Submit Handlers для Form Engine.

Содержит обработчики отправки форм, которые интегрируются
с бизнес-логикой приложения (Bitrix24, БД, PDF и т.д.).

Каждый handler регистрируется для конкретного form_id.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os

from aiogram.types import FSInputFile

from main.forms.engine import register_submit_handler
from main.forms.schemas import FormConfig, FormState, FormSubmitResult
from main.config.log_config import logger
from main.config.bot_config import bot


@register_submit_handler("activation")
async def handle_activation_submit(
    data: Dict[str, Any], 
    state: FormState, 
    config: FormConfig
) -> FormSubmitResult:
    """
    Обработчик отправки формы активации гарантии.
    
    Выполняет:
    1. Сохранение/обновление пользователя в БД
    2. Создание устройства
    3. Создание гарантии
    4. Отправка в Bitrix24
    5. Генерация и отправка PDF сертификата
    6. Отправка памятки
    
    :param data: Собранные данные формы
    :param state: Состояние формы
    :param config: Конфигурация формы
    :return: FormSubmitResult
    """
    from main.service.model.user_service import UserService
    from main.service.model.device_service import DeviceService
    from main.service.model.guarantee_service import GuaranteeService
    from main.model.guarantee_base import GuaranteeBase
    from main.dto.guarantee_request_dto import GuaranteeCreateBitrix24RequestDTO
    from main.dto.guarantee_response_dto import GuaranteeResponseDTO
    from main.enum.guarantee_enum import GuaranteeTypeEnum
    from main.service.integration.pdf_service import generate_certificate_pdf
    
    user_service = UserService()
    device_service = DeviceService()
    guarantee_service = GuaranteeService()
    
    try:
        logger.info(f"Processing activation form for user {state.user_id}", extra={"service": "form_engine"})
        
        # 1. Получаем или создаём пользователя
        user = await user_service.get_user(state.chat_id)
        if not user:
            user = await user_service.create_user(
                chat_id=state.chat_id,
                username=None,
                full_name=f"{data.get('surname', '')} {data.get('name', '')}"
            )
        
        # 2. Обновляем данные пользователя из формы
        user.name = data.get('name')
        user.surname = data.get('surname')
        user.phone = data.get('phone')
        user.email = data.get('email')
        user.city = data.get('city')
        user.order_source = data.get('order_source')
        user.pd_consent = data.get('pd_consent', False)
        user.marketing_consent = data.get('marketing_consent', False)
        
        user = await user_service.update_user(user)
        logger.info(f"User {user.chat_id} updated", extra={"service": "form_engine"})
        
        # 3. Создаём устройство
        device = await device_service.create_device_simple(
            serial_number=None, 
            user_id=state.user_id
        )
        logger.info(f"Device {device.id} created", extra={"service": "form_engine"})
        
        # 4. Создаём гарантию
        guarantee_base = GuaranteeBase()
        await guarantee_base.enrich_from_inline_keyboard(
            device_id=device.id,
            guarantee_type="standard",
            guarantee_standard_price=0
        )
        
        device_with_guarantees = await device_service.get_device_with_guarantee(device.id)
        
        # Проверяем дубликат гарантии
        has_standard = any(
            g.guarantee_type == GuaranteeTypeEnum.STANDARD 
            for g in device_with_guarantees.guarantees
        )
        if has_standard:
            return FormSubmitResult(
                success=False,
                error="У вас уже есть стандартная гарантия на это устройство."
            )
        
        guarantee = await guarantee_service.create_guarantee_with_period(
            guarantee_base, 
            device_with_guarantees
        )
        logger.info(f"Guarantee {guarantee.id} created", extra={"service": "form_engine"})
        
        # 5. Отправляем в Bitrix24
        try:
            guarantee_dto = GuaranteeCreateBitrix24RequestDTO(
                guarantee, 
                device_with_guarantees, 
                user
            )
            await guarantee_service.create_guarantee_deal_in_bitrix24(guarantee_dto)
            logger.info("Deal created in Bitrix24", extra={"service": "form_engine"})
        except Exception as e:
            logger.error(f"Failed to create Bitrix24 deal: {e}", extra={"service": "form_engine"})
            # Не прерываем процесс — Bitrix не критичен
        
        # 6. Генерируем и отправляем PDF сертификат
        pdf_path = None
        try:
            pdf_path = generate_certificate_pdf(
                user=user, 
                device=device_with_guarantees, 
                guarantee=guarantee
            )
            await bot.send_document(
                state.chat_id,
                FSInputFile(pdf_path),
                caption="🎓 Цифровой гарантийный сертификат"
            )
            logger.info("Certificate PDF sent", extra={"service": "form_engine"})
        except Exception as e:
            logger.error(f"Failed to send certificate PDF: {e}", extra={"service": "form_engine"})
        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
        
        # 7. Отправляем памятку
        try:
            memo_path = Path(__file__).resolve().parents[2] / "resources" / "Setka_Garmoshka_Памятка_гарантия_шины.pdf"
            if memo_path.exists():
                await bot.send_document(
                    state.chat_id,
                    FSInputFile(str(memo_path)),
                    caption="📋 Памятка по гарантии"
                )
                logger.info("Memo PDF sent", extra={"service": "form_engine"})
        except Exception as e:
            logger.error(f"Failed to send memo PDF: {e}", extra={"service": "form_engine"})
        
        # Формируем информацию о гарантии для сообщения
        guarantee_response = GuaranteeResponseDTO(guarantee, device_with_guarantees)
        guarantee_text = await guarantee_response.get_guarantee_text()
        
        return FormSubmitResult(
            success=True,
            message=f"✅ *Спасибо за активацию гарантии!*\n\n{guarantee_text}",
            data={
                "user_id": user.chat_id,
                "device_id": device.id,
                "guarantee_id": guarantee.id
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing activation form: {e}", extra={"service": "form_engine"})
        return FormSubmitResult(
            success=False,
            error=str(e)
        )


# Дополнительные handlers можно добавлять здесь
# Пример:
#
# @register_submit_handler("feedback")
# async def handle_feedback_submit(data, state, config):
#     # Обработка формы обратной связи
#     return FormSubmitResult(success=True)
