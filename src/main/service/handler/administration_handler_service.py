from main.model.device_base import DeviceBase
from main.service.model.device_service import DeviceService
from main.service.model.guarantee_service import GuaranteeService


device_service = DeviceService()
guarantee_service = GuaranteeService()


async def delete_guarantees_and_device_by_serial_number(serial_number):
    """
    Метод проставляет признак is_deleted = True устройству и всем его гарантийным планам

    :param serial_number: серийный номер устройства
    """

    # Получаем устройство
    device: DeviceBase = await device_service.get_device_by_serial_number(serial_number)

    # Удаляем устройство и его гарантийные планы
    await device_service.delete_device(device)
    await guarantee_service.delete_guarantees_by_device_id(device.id)
