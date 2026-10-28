
import os
import requests
from django.conf import settings

def send_telegram_msg(
    message: str, 
    file=None, 
    file_bytes=None,
    filename: str = "document",
    chat_id: str = settings.SETTING_TELEGRAM_CHAT_ID, 
    bot_token: str = settings.TELEGRAM_BOT_TOKEN, 
    disable_notification: bool = False, 
    parse_mode: str = "HTML",
    as_document: bool = False,
    show_caption_above_media: bool = False,
):
    
    params = {
        "chat_id": chat_id,
        "parse_mode": parse_mode,
        "disable_notification": disable_notification,
    }

    if show_caption_above_media:
        params["show_caption_above_media"] = True

    target_file = file_bytes if file_bytes else file

    try:
        if target_file:
            # Вытаскиваем расширение (.jpg, .tar.gz и т.д.)
            ext = os.path.splitext(filename)[1].lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.jfif']

            params["caption"] = message

            if ext in image_extensions and not as_document:
                # РЕЖИМ ФОТО: Если расширение картинки — шлем красиво и раскрыто
                files = {"photo": (filename, target_file, f"image/{ext.replace('.', '')}")}
                url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            else:
                # РЕЖИМ ДОКУМЕНТА: Если это архив бэкапа, база .sql или документ
                files = {"document": (filename, target_file, "application/octet-stream")}
                url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            
            # Отправляем в Телеграм
            response = requests.post(url, data=params, files=files, timeout=10)
            
        else:
            # Если файла нет — шлем обычный текст (заявку или лог спама)
            params["text"] = message
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            response = requests.post(url, data=params, timeout=10)
            
        print("Done: Telegram notification sent")
        return response
    except Exception as e:
        print(f"NO Done: {e}")
        return None