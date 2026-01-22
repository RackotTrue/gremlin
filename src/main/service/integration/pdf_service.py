from datetime import datetime
from pathlib import Path
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.units import mm

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _safe(value):
    return value if value is not None else ""


# Регистрируем шрифт Times New Roman с кириллицей
FONT_NAME = "TimesNewRoman"
# Ищем Times New Roman в системных папках
TIMES_FONT_PATHS = [
    Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
    Path("/Library/Fonts/Times New Roman.ttf"),
    Path("/System/Library/Fonts/Times.ttc"),
    Path("/Library/Fonts/Times.ttc"),
]

FONT_PATH = None
FONT_REGISTERED = False

# Ищем Times New Roman в системе
for font_path in TIMES_FONT_PATHS:
    if font_path.exists():
        try:
            # Для .ttc файлов нужно указать индекс (обычно 0)
            if font_path.suffix == '.ttc':
                # TTC файлы требуют специальной обработки, попробуем TTF
                continue
            pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
            FONT_PATH = font_path
            FONT_REGISTERED = True
            break
        except Exception as e:
            continue

# Если Times New Roman не найден, используем встроенный Times-Roman
if not FONT_REGISTERED:
    FONT_NAME = "Times-Roman"  # Встроенный шрифт ReportLab


def generate_certificate_pdf(user, device, guarantee) -> Path:
    """
    Генерирует PDF сертификат и возвращает путь к файлу.
    Файл создаётся во временной директории /tmp/setka_garmoshka_bot.
    """
    tmp_dir = Path("/tmp/setka_garmoshka_bot")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    filename = f"certificate_{user.chat_id}_{device.id}.pdf"
    pdf_path = tmp_dir / filename

    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    width, height = A4
    
    # Цвета (синий для оформления)
    blue_color = colors.HexColor('#1E3A8A')  # Темно-синий
    light_blue = colors.HexColor('#E0F2FE')  # Светло-синий для фона
    white = colors.white
    
    # Рисуем синюю рамку
    border_width = 15
    c.setStrokeColor(blue_color)
    c.setFillColor(blue_color)
    c.setLineWidth(border_width)
    c.rect(border_width/2, border_width/2, width - border_width, height - border_width, fill=0, stroke=1)
    
    # Рисуем фон (светло-синий градиент)
    c.setFillColor(light_blue)
    c.rect(border_width, border_width, width - border_width*2, height - border_width*2, fill=1, stroke=0)
    
    # Белый фон для основного контента
    content_margin = 30
    content_y_start = height - 200
    content_height = content_y_start - 100
    c.setFillColor(white)
    c.rect(content_margin, 100, width - content_margin*2, content_height, fill=1, stroke=0)
    
    # Добавляем логотип в правый верхний угол
    logo_path = Path(__file__).resolve().parents[3] / "resources" / "logo.png"
    
    if logo_path.exists():
        try:
            logo_size = 70
            logo_x = width - logo_size - content_margin
            logo_y = height - logo_size - content_margin
            
            if PIL_AVAILABLE:
                img = Image.open(str(logo_path))
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                c.drawImage(ImageReader(img), logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True)
            else:
                c.drawImage(str(logo_path), logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True)
        except Exception as e:
            print(f"Ошибка при добавлении логотипа: {e}")
    
    # Заголовок "ГАРАНТИЙНЫЙ СЕРТИФИКАТ" в синей полосе
    title_bar_height = 50
    title_y = height - 120
    c.setFillColor(blue_color)
    c.rect(content_margin, title_y - title_bar_height, width - content_margin*2, title_bar_height, fill=1, stroke=0)
    
    c.setFillColor(white)
    c.setFont(FONT_NAME, 24)
    title_text = "ГАРАНТИЙНЫЙ СЕРТИФИКАТ"
    title_width = c.stringWidth(title_text, FONT_NAME, 24)
    c.drawString((width - title_width) / 2, title_y - title_bar_height + 15, title_text)
    
    # Основной контент
    y = title_y - title_bar_height - 40
    c.setFillColor(colors.black)
    c.setFont(FONT_NAME, 14)
    
    # Форматируем даты
    start_date_str = guarantee.start_date.strftime("%d.%m.%Y") if guarantee.start_date else "не указана"
    end_date_str = guarantee.end_date.strftime("%d.%m.%Y") if guarantee.end_date else "не указана"
    
    # Поля с подчеркиванием
    field_x = content_margin + 20
    field_width = width - content_margin*2 - 40
    line_y_offset = 15
    
    # ФИО
    c.setFont(FONT_NAME, 12)
    c.drawString(field_x, y, "ФИО:")
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(field_x + 60, y + line_y_offset, field_x + field_width, y + line_y_offset)
    c.drawString(field_x + 70, y, f"{_safe(user.surname)} {_safe(user.name)}")
    y -= 35
    
    # Телефон
    c.drawString(field_x, y, "Телефон:")
    c.line(field_x + 80, y + line_y_offset, field_x + field_width, y + line_y_offset)
    c.drawString(field_x + 90, y, f"{_safe(user.phone)}")
    y -= 35
    
    # Email
    c.drawString(field_x, y, "Email:")
    c.line(field_x + 60, y + line_y_offset, field_x + field_width, y + line_y_offset)
    c.drawString(field_x + 70, y, f"{_safe(user.email)}")
    y -= 35
    
    # Срок действия
    c.drawString(field_x, y, "Срок действия:")
    c.line(field_x + 120, y + line_y_offset, field_x + field_width, y + line_y_offset)
    c.drawString(field_x + 130, y, f"{start_date_str} — {end_date_str}")
    y -= 50
    
    # Информационный текст
    c.setFont(FONT_NAME, 11)
    info_text = "Сохраните этот сертификат — он подтверждает вашу гарантию."
    c.drawString(field_x, y, info_text)
    y -= 20
    
    # Контакты поддержки (синим цветом)
    c.setFillColor(blue_color)
    c.setFont(FONT_NAME, 11)
    support_text = "Контакты поддержки: @setka_garmoshka"
    c.drawString(field_x, y, support_text)

    c.showPage()
    c.save()

    return pdf_path

