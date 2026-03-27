import os
import hashlib
import yt_dlp
import time
import asyncio
from aiogram.types import FSInputFile
from yt_dlp.utils import ExtractorError, UnsupportedError


def generate_url_id(url: str):
    return hashlib.md5(url.encode()).hexdigest()


async def download_and_send_media(bot, chat_id, url, media_type):
    filename = None

    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'retries': 3,
            'socket_timeout': 60,
            'extractor_retries': 3,

            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'en-US,en;q=0.9',
            },

            # если появятся cookies — будет работать лучше
            'cookiefile': 'cookies.txt',
        }

        # 🎬 ВЫБОР ФОРМАТА
        if media_type == 'video':
            if any(site in url for site in ["pinterest", "vk"]):
                ydl_opts['format'] = 'best'
            else:
                ydl_opts['format'] = (
                    'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/'
                    'best[ext=mp4][height<=720]/'
                    'best'
                )

        start_time = time.time()

        loop = asyncio.get_event_loop()

        info = await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True)
        )

        ydl = yt_dlp.YoutubeDL(ydl_opts)
        filename = ydl.prepare_filename(info)

        # 🎧 фиксим аудио расширение
        if media_type == 'audio':
            base = os.path.splitext(filename)[0]
            for ext in ['.m4a', '.mp3', '.webm']:
                if os.path.exists(base + ext):
                    filename = base + ext
                    break

        # 🎥 FIX WEBM → MP4
        if filename.endswith('.webm'):
            new_filename = filename.replace('.webm', '.mp4')
            os.system(f'ffmpeg -i "{filename}" -c:v libx264 -c:a aac "{new_filename}"')
            os.remove(filename)
            filename = new_filename

        if not filename or not os.path.exists(filename):
            raise FileNotFoundError("Файл не найден")

        file_size = os.path.getsize(filename)

        # 💥 ЕСЛИ ФАЙЛ БОЛЬШОЙ
        if file_size > 50 * 1024 * 1024:
            await bot.send_message(
                chat_id,
                "📦 Видео слишком большое для Telegram.\n"
                f"Вот ссылка:\n{url}"
            )
            return

        elapsed_time = time.time() - start_time
        media_file = FSInputFile(filename)

        # 📤 ОТПРАВКА
        if media_type == "video":
            await bot.send_video(chat_id, media_file, caption=f"⏱ {elapsed_time:.1f} сек")
        else:
            await bot.send_audio(chat_id, media_file, caption=f"⏱ {elapsed_time:.1f} сек")

        os.remove(filename)

    except (ExtractorError, UnsupportedError) as e:
        await bot.send_message(chat_id, "❌ Не удалось скачать (возможно сайт изменился)")
        print(f"[YT-DLP ERROR] {e}")

    except Exception as e:
        await bot.send_message(chat_id, "⚠️ Ошибка. Попробуй другую ссылку")
        print(f"[ERROR] {e}")

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass