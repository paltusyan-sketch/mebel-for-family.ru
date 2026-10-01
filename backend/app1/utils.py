
import os
import requests
from django.conf import settings

def send_telegram_msg(
    message: str, 
    file=None, 
    filename: str = "document",
    chat_id: str = settings.SETTING_TELEGRAM_CHAT_ID, 
    bot_token: str = settings.TELEGRAM_BOT_TOKEN, 
    disable_notification: bool = False, 
    parse_mode: str = "HTML",
    as_document: bool = False
):
    
    params = {
        "chat_id": chat_id,
        "parse_mode": parse_mode,
        "disable_notification": disable_notification,
    }

    try:
        if file:
            # Вытаскиваем расширение (.jpg, .tar.gz и т.д.)
            ext = os.path.splitext(filename)[1].lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.jfif']

            if ext in image_extensions and not as_document:
                # РЕЖИМ ФОТО: Если расширение картинки — шлем красиво и раскрыто
                params["caption"] = message
                files = {"photo": (filename, file, f"image/{ext.replace('.', '')}")}
                url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            else:
                # РЕЖИМ ДОКУМЕНТА: Если это архив бэкапа, база .sql или документ
                params["caption"] = message
                files = {"document": (filename, file, "application/octet-stream")}
                url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            
            # Отправляем в Телеграм
            requests.post(url, data=params, files=files, timeout=10)
            
        else:
            # Если файла нет — шлем обычный текст (заявку или лог спама)
            params["text"] = message
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, data=params, timeout=10)
            
        print("Done: Telegram notification sent")
    except Exception as e:
        print(f"NO Done: {e}")
        pass