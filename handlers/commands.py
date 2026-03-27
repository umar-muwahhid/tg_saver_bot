from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import keyboards.inline_kb as in_kb
import handlers.function as hf
import url_storage as storage

router = Router()

# ✅ Список поддерживаемых доменов
SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",      # YouTube
    "tiktok.com",                   # TikTok
    "instagram.com", "instagr.am",  # Instagram
    "vk.com", "vk.ru",              # ВКонтакте
    "pinterest.com", "pin.it"       # Pinterest
]

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(
        "Привет! Отправь мне ссылку на видео из:\n"
        "📺 YouTube\n"
        "🎵 TikTok\n"
        "📸 Instagram\n"
        "🎬 ВКонтакте\n"
        "📌 Pinterest\n\n"
        "Я помогу скачать его без водяных знаков!"
    )

@router.message(lambda msg: msg.text and any(domain in msg.text for domain in SUPPORTED_DOMAINS))
async def video_request(message: Message):
    url = message.text.strip()
    url_id = hf.generate_url_id(url)
    storage.url_storage[url_id] = url
    storage.save_url_storage(storage.url_storage)
    
    # Проверяем, поддерживает ли сайт выбор формата
    if "instagram.com" in url or "pinterest.com" in url:
        # Для этих сайтов часто доступен только видеоформат
        await message.answer("Начинаю обработку...", reply_markup=await in_kb.format_btn(url_id))
    else:
        await message.answer("Выберите формат загрузки:", reply_markup=await in_kb.format_btn(url_id))