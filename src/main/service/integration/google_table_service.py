from typing import List, Dict
from gspread import Spreadsheet

from main.config.log_config import logger


class GoogleTableService():


    async def get_data_from_sheet(self, table: Spreadsheet, sheet_name: str = "Лист1") -> List[Dict]:
        """
        Извлекает данные из указанного листа таблицы Google Sheets и возвращает список словарей.

        :param table: Объект таблицы Google Sheets (Spreadsheet).
        :param sheet_name: Название листа в таблице.
        :return: Список словарей, представляющих данные из таблицы.
        """

        try:
            data = []
            worksheet = table.worksheet(sheet_name)

            # Выбираем строку, которая считается заголовком
            headers = worksheet.row_values(13)
            # Выбираем с какой строки начинаем считывать данные
            rows = worksheet.get_all_values()[13:]

            for row in rows:
                row_dict = {headers[i]: value.strip() for i, value in enumerate(row)}
                data.append(row_dict)

            return data

        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из таблицы Google: {e}", extra={"service": "google_table"})

