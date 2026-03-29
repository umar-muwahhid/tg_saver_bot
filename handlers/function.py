import os
import hashlib
import yt_dlp
import time
import asyncio
import subprocess
from aiogram.types import FSInputFile
from yt_dlp.utils import ExtractorError, UnsupportedError


def generate_url_id(url: str):
    return hashlib.md5(url.encode()).hexdigest()


async def download_and_send_media(bot, chat_id, url, media_type):
    filename = None

    # 🔥 FIX YOUTUBE SHORTS → NORMAL URL
    if "youtube.com/shorts/" in url:
        video_id = url.split("/shorts/")[1].split("?")[0]
        url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,

            'retries': 10,
            'fragment_retries': 10,
            'extractor_retries': 10,

            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'en-US,en;q=0.9',
            },

            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },

            'cookiefile': 'cookies.txt',

            'hls_prefer_native': True,
        }

        # 🎬 ВЫБОР ФОРМАТА
        if media_type == 'video':
            ydl_opts['format'] = 'bestvideo+bestaudio/best/bestvideo/best'
        elif media_type == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
        }]

        start_time = time.time()

        loop = asyncio.get_event_loop()

        try:
            info = await loop.run_in_executor(
                None,
                lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True)
            )
        except Exception:
            # 💥 fallback для YouTube
            if "youtube" in url or "youtu.be" in url:
                ydl_opts['format'] = 'worst[ext=mp4]/worst'
                info = await loop.run_in_executor(
                    None,
                    lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True)
                )
            else:
                raise
        if not info:
            raise Exception("Не удалось получить информацию о видео")

        ydl = yt_dlp.YoutubeDL(ydl_opts)
        filename = ydl.prepare_filename(info)

        # 🎥 FIX WEBM → MP4
        if filename.endswith('.webm'):
            new_filename = filename.replace('.webm', '.mp4')
            subprocess.run([
                "ffmpeg",
                "-i", filename,
                "-c:v", "libx264",
                "-c:a", "aac",
                new_filename
            ])       
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