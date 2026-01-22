# Google Sheets отключен - верификация товаров не требуется
# 
# Если в будущем потребуется включить Google Sheets:
# 1. Создать Service Account в Google Cloud Console
# 2. Скачать JSON файл с credentials
# 3. Положить файл в resources/properties/
# 4. Добавить в application_properties.yaml:
#    google:
#      application_file_name: "your-credentials.json"
#      device_table_id: "YOUR_TABLE_ID"
# 5. Раскомментировать код ниже:
#
# from gspread import Client, Spreadsheet, service_account
# from main.config.dynaconf_config import config_setting
#
# google_client: Client = service_account(filename="resources/properties/" + config_setting.GOOGLE.APPLICATION_FILE_NAME)
# table: Spreadsheet = google_client.open_by_key(config_setting.GOOGLE.DEVICE_TABLE_ID)

# Заглушки - Google таблицы отключены
google_client = None
table = None
