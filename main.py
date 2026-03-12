import asyncio
import aiohttp

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8648830104:AAEc8EFi1lqoOCMLh5N4UxxbHoVtOsSEL84"

API_URL = "https://api.delirius.store/download/instagram?url="

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 <b>Instagram Downloader Bot</b>\n\n"
        "Send me an Instagram link and I will download the media for you."
    )


async def fetch_instagram_data(url: str):
    api = f"{API_URL}{url}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api) as response:
            return await response.json()


@dp.message()
async def download_instagram(message: Message):
    url = message.text.strip()

    if "instagram.com" not in url:
        await message.reply("❌ Please send a valid Instagram link.")
        return

    status_msg = await message.reply("⏳ Downloading media...")

    try:
        data = await fetch_instagram_data(url)

        if not data.get("status"):
            await status_msg.edit_text("❌ Failed to fetch media.")
            return

        media_list = data.get("data", [])

        if not media_list:
            await status_msg.edit_text("❌ No media found.")
            return

        media_group = []

        for media in media_list:
            media_url = media["url"]
            media_type = media["type"]

            if media_type == "image":
                media_group.append(InputMediaPhoto(media=media_url))

            elif media_type == "video":
                media_group.append(InputMediaVideo(media=media_url))

        await status_msg.delete()

        # Telegram limit: max 10 items per media group
        for i in range(0, len(media_group), 10):
            await message.answer_media_group(media_group[i:i + 10])

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")


async def main():
    print("🚀 Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
