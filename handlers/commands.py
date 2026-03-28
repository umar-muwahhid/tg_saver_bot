from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import keyboards.inline_kb as in_kb
import handlers.function as hf
import url_storage as storage

router = Router()

# ❌ Instagram временно убран (он ломается без cookies)
SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com",
    "vk.com", "vk.ru",
    "pinterest.com", "pin.it"
]

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(
        "Привет! Отправь ссылку:\n"
        "📺 YouTube\n"
        "🎵 TikTok\n"
        "🎬 VK\n"
        "📌 Pinterest\n"
        "Instagramchick"
    )

@router.message(lambda msg: msg.text and any(domain in msg.text for domain in SUPPORTED_DOMAINS))
async def video_request(message: Message):
    url = message.text.strip()

    url_id = hf.generate_url_id(url)
    storage.url_storage[url_id] = url
    storage.save_url_storage(storage.url_storage)

    await message.answer(
        "Выберите формат:",
        reply_markup=await in_kb.format_btn(url_id)
    )