
import os
import requests
from django.conf import settings
from celery import shared_task
import subprocess
from django.utils import timezone
from .utils import send_telegram_msg


# @shared_task(bind=True, default_retry_delay=5*60, max_retries=3)
# def send_telegram_msg(
#     self,
#     message: str, 
#     file=None, 
#     filename: str = "document",
#     chat_id: str = settings.SETTING_TELEGRAM_CHAT_ID, 
#     bot_token: str = settings.TELEGRAM_BOT_TOKEN, 
#     disable_notification: bool = False, 
#     parse_mode: str = "HTML",
#     as_document: bool = False
# ):
    
#     params = {
#         "chat_id": chat_id,
#         "parse_mode": parse_mode,
#         "disable_notification": disable_notification,
#     }

#     try:
#         if file:
#             # Вытаскиваем расширение (.jpg, .tar.gz и т.д.)
#             ext = os.path.splitext(filename)[1].lower()
#             image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.jfif']

#             if ext in image_extensions and not as_document:
#                 # РЕЖИМ ФОТО: Если расширение картинки — шлем красиво и раскрыто
#                 params["caption"] = message
#                 files = {"photo": (filename, file, f"image/{ext.replace('.', '')}")}
#                 url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
#             else:
#                 # РЕЖИМ ДОКУМЕНТА: Если это архив бэкапа, база .sql или документ
#                 params["caption"] = message
#                 files = {"document": (filename, file, "application/octet-stream")}
#                 url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            
#             # Отправляем в Телеграм
#             requests.post(url, data=params, files=files, timeout=10)
            
#         else:
#             # Если файла нет — шлем обычный текст (заявку или лог спама)
#             params["text"] = message
#             url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
#             requests.post(url, data=params, timeout=10)
            
#         print("Done: Telegram notification sent\nФоновая задача Celery успешно выполнена")
        
#     except Exception as exc:
#         print(f"Ошибка сети в Celery воркере: {exc}. Перезапуск задачи...")
#         # Если упал интернет на Beget, Celery сама попробует отправить сообщение еще раз через 5 минут!
#         raise self.retry(exc=exc)



@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def telegram_backup_task(self, username):
    current_time = timezone.localtime(timezone.now()).strftime("%d.%m.%Y %H:%M")
    file_time_str = timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H-%M")

    # Переименовываем имя архива в фоне, чтобы он не затирал ручной бэкап в /app/
    archive_path = f"/app/telegram_backup_{file_time_str}.tar.gz"
    db_sql_path = "/app/backup_db.sql"

    db_config = settings.DATABASES['default']
    db_name = db_config['NAME']
    db_user = db_config['USER']
    db_password = db_config['PASSWORD']
    db_host = db_config.get('HOST', 'db')

    cmd = (
        f"pg_dump -h {db_host} -U {db_user} -d {db_name} > {db_sql_path} && "
        f"tar -czf {archive_path} -C /app/ backup_db.sql && "
        f"rm -f {db_sql_path}"
    )

    try:
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password

        subprocess.run(cmd, shell=True, check=True, env=env)

        if os.path.exists(archive_path) and os.path.getsize(archive_path) > 0:
            size_bytes = os.path.getsize(archive_path)
            size_mb = size_bytes / (1024 * 1024)
            backup_weight = f"{size_bytes / 1024:.1f}KB" if size_mb < 1.0 else f"{size_mb:.2f}MB"

            # 1. ОТПРАВЛЯЕМ ТЕКСТОВЫЙ ЛОГ О СБОРКЕ
            log_message = (
                f"<b>📦 Резервное копирование UralMeb</b>\n\n"
                f"<b>⚙️ Тип:</b> <code>🚀 Отправка в Telegram (Celery)</code>\n"
                f"<b>👤 Инициатор:</b> {username}\n"
                f"<b>📅 Дата:</b> {current_time}\n"
                f"<b>⚖️ Вес:</b> <code>{backup_weight}</code>\n"
                f"<b>🗄 Состав:</b> База данных (SQL)"
            )

            # 2. ОТПРАВЛЯЕМ САМ ТЯЖЁЛЫЙ ФАЙЛ АРХИВА ДОКУМЕНТОМ В ТЕЛИК
            # Открываем готовый архив с диска на чтение бинарника ('rb')
            with open(archive_path, 'rb') as backup_file:
                bytes_data = backup_file.read()

                # Метод sendDocument отправит 61 МБ файл байт-в-байт в Телеграм без потери структуры
                log_res = send_telegram_msg(
                    message=log_message,
                    file_bytes=bytes_data,
                    filename=f"backup_SQL_{file_time_str}.tar.gz",
                    as_document=True
                )
                print("LOG_BACKUP_TELEGRAM"+f"--- TG TEXT STATUS: {log_res.status_code} ---")
                print("LOG_BACKUP_TELEGRAM"+f"--- TG TEXT RESPONSE: {log_res.text} ---")
                if log_res is None or log_res.status_code != 200:
                    raise Exception("Telegram API вернул ошибку")

            # 3. НАЧИСТО УДАЛЯЕМ АРХИВ С СЕРВЕРА (Защита от засирания памяти)
            if os.path.exists(archive_path):
                os.remove(archive_path)
                
            return "Success"
        else:
            raise Exception("Архив пустой")

    except Exception as e:
        error_msg = f"🔴 Ошибка фонового бэкапа: {e}"
        print(error_msg)
        log_res = send_telegram_msg(message=error_msg)

        print("LOG_BACKUP_TELEGRAM"+f"--- TG TEXT STATUS: {log_res.status_code} ---")
        print("LOG_BACKUP_TELEGRAM"+f"--- TG TEXT RESPONSE: {log_res.text} ---")

        if self.request.retries >= 5 and os.path.exists(archive_path):
            os.remove(archive_path)

        raise self.retry(exc=e, countdown=15)