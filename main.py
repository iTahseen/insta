import asyncio
import aiohttp
import os
import uuid

from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
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
        "👋 <b>Instagram Downloader</b>\n\n"
        "Send me an Instagram link."
    )


async def fetch_instagram(url: str):
    api = f"{API_URL}{url}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api) as resp:
            return await resp.json()


async def download_file(url):
    filename = f"media_{uuid.uuid4().hex}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            content = await resp.read()

    with open(filename, "wb") as f:
        f.write(content)

    return filename


@dp.message()
async def downloader(message: Message):

    url = message.text.strip()

    if "instagram.com" not in url:
        await message.reply("❌ Send a valid Instagram link.")
        return

    status = await message.reply("⏳ Downloading media...")

    try:
        data = await fetch_instagram(url)

        if not data.get("status"):
            await status.edit_text("❌ Failed to fetch media.")
            return

        media_list = data.get("data", [])

        await status.edit_text("📥 Downloading files...")

        files = []

        for media in media_list:
            file_path = await download_file(media["url"])
            files.append((file_path, media["type"]))

        await status.edit_text("⬆ Uploading to Telegram...")

        for file_path, media_type in files:

            file = FSInputFile(file_path)

            if media_type == "video":
                await message.answer_video(file)

            elif media_type == "image":
                await message.answer_photo(file)

            else:
                await message.answer_document(file)

            os.remove(file_path)

        await status.delete()

    except Exception as e:
        await message.reply(f"❌ Error: {e}")


async def main():
    print("🚀 Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
