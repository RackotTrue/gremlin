from dynaconf import Dynaconf
from types import SimpleNamespace
from pathlib import Path

def dict_to_namespace(d):
    """Рекурсивно преобразует словарь в SimpleNamespace с верхним регистром ключей"""
    if isinstance(d, dict):
        return SimpleNamespace(**{k.upper(): dict_to_namespace(v) for k, v in d.items()})
    return d

# Получаем путь к файлам конфигурации
config_path = Path(__file__).parent.parent.parent / "resources" / "properties"

# Парсинг файла с окружением через Dynaconf
environment_setting = Dynaconf(
    settings_files=[str(config_path / "env.yaml")],
    core_loaders=['YAML']
)

# Получаем текущее окружение через to_dict
env_dict = environment_setting.to_dict()
current_environment = env_dict.get('environment', 'development')

# Парсинг файла с настроечными конфигурациями
app_config = Dynaconf(
    settings_files=[str(config_path / "application_properties.yaml")],
    core_loaders=['YAML']
)

# Получаем конфигурацию для текущего окружения через to_dict
# Dynaconf преобразует ключи в верхний регистр
app_dict = app_config.to_dict()
env_config_dict = app_dict.get(current_environment.upper(), {})

# Преобразуем в объект с атрибутами
config_setting = dict_to_namespace(env_config_dict)

# Парсинг файла с id администраторов
security_setting = Dynaconf(
    settings_files = ["resources/properties/admin_id.yaml"],
    core_loaders=['YAML']
)