import os
import hashlib
import yt_dlp
import time
import glob
from aiogram.types import FSInputFile
from yt_dlp.utils import ExtractorError, UnsupportedError

def generate_url_id(url: str):
    """Генерирует уникальный ID для ссылки"""
    return hashlib.md5(url.encode()).hexdigest()

async def download_and_send_media(bot, chat_id, url, media_type):
    """Скачивает и отправляет медиа пользователю"""
    
    filename = None
    
    try:
        # 🔧 Базовые настройки yt_dlp (универсальные, без куки)
        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',  # Имя файла = ID видео
            'noplaylist': True,                      # Не качать плейлисты целиком
            'quiet': True,                           # Тихий режим
            'no_warnings': True,                     # Не показывать предупреждения
            'retries': 2,                            # Повтор при сбое
            'socket_timeout': 20,                    # Таймаут соединения
            'extract_flat': False,                   # Полная экстракция информации
            
            # 🎭 Маскировка под обычный браузер
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        # 🎬 Выбор формата в зависимости от типа
        if media_type == 'video':
            # Пробуем получить mp4, если нет — лучшее доступное
            ydl_opts['format'] = 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio/best'
        else:
            # Для аудио: m4a предпочтительнее, потом mp3, потом любое
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '192',
            }]

        start_time = time.time()

        # 🚀 Запуск загрузки
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id', 'unknown')
            
            # 🔍 Ищем скачанный файл
            possible_files = glob.glob(f"downloads/{video_id}.*")
            if possible_files:
                filename = possible_files[0]
            else:
                filename = ydl.prepare_filename(info)
                # Если расширение могло измениться после конвертации аудио
                if media_type == 'audio' and filename.endswith('.webm'):
                    filename = filename.rsplit('.', 1)[0] + '.m4a'

        elapsed_time = time.time() - start_time

        # ❌ Проверка: файл действительно существует?
        if not filename or not os.path.exists(filename):
            raise FileNotFoundError("Файл не найден после загрузки")

        # 📦 Проверка размера (лимит Telegram ~50 МБ)
        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            os.remove(filename)
            await bot.send_message(chat_id, "📦 Файл слишком большой (>50 МБ). Попробуйте видео покороче.")
            return

        # 📤 Отправка файла
        media_file = FSInputFile(filename)
        caption = f"⏱ Обработано за {elapsed_time:.1f} сек."
        
        if media_type == "video":
            await bot.send_video(chat_id, media_file, caption=caption)
        else:
            await bot.send_audio(chat_id, media_file, caption=caption)
            
        # 🧹 Удаляем файл после отправки
        os.remove(filename)

    # 🔥 Обработка ошибок yt-dlp (красивые сообщения для пользователя)
    except (ExtractorError, UnsupportedError) as e:
        error_msg = str(e).lower()
        
        if "ip address is blocked" in error_msg or "blocked from accessing" in error_msg:
            await bot.send_message(chat_id, "🚫 Видео недоступно: сервер временно заблокирован. Попробуйте другую ссылку.")
        elif "private" in error_msg or "unavailable" in error_msg or "not found" in error_msg or "404" in error_msg:
            await bot.send_message(chat_id, "🔒 Видео удалено, приватно или ссылка неверна.")
        elif "timeout" in error_msg or "connection" in error_msg or "network" in error_msg:
            await bot.send_message(chat_id, "🌐 Ошибка сети. Проверьте соединение и попробуйте снова.")
        elif "ffmpeg" in error_msg and media_type == "audio":
            await bot.send_message(chat_id, "🎵 Для извлечения аудио нужен FFmpeg. Установите его или попробуйте скачать видео.")
        else:
            await bot.send_message(chat_id, "❌ Не удалось скачать видео. Возможно, ссылка устарела или формат не поддерживается.")
        
        # Полная ошибка — только в консоль разработчика
        print(f"[YT-DLP ERROR] {e}")

    except FileNotFoundError:
        await bot.send_message(chat_id, "📁 Ошибка сохранения файла. Попробуйте ещё раз.")
        print(f"[FILE ERROR] Not found: {filename}")

    except Exception as e:
        # Любая другая ошибка — универсальный ответ
        await bot.send_message(chat_id, "⚠️ Произошла ошибка. Попробуйте другую ссылку.")
        print(f"[UNKNOWN ERROR] {type(e).__name__}: {e}")
        
    finally:
        # 🧽 Гарантированная очистка: удаляем файл, если он остался
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as cleanup_err:
                print(f"[CLEANUP ERROR] {cleanup_err}")