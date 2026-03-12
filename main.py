import asyncio
import aiohttp
import os
import uuid
import subprocess

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


# START COMMAND
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 <b>Instagram Downloader</b>\n\n"
        "Send an Instagram link and I will download the media."
    )


# FETCH INSTAGRAM DATA
async def fetch_instagram(url: str):

    api = f"{API_URL}{url}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api) as resp:
            return await resp.json()


# STREAM DOWNLOAD FILE
async def download_file(url):

    filename = f"/tmp/{uuid.uuid4().hex}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:

            with open(filename, "wb") as f:

                async for chunk in resp.content.iter_chunked(1024 * 256):
                    f.write(chunk)

    return filename


# CREATE VIDEO THUMBNAIL
def create_thumbnail(video_path):

    thumb = f"{video_path}.jpg"

    command = [
        "ffmpeg",
        "-ss", "00:00:01",
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        thumb
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return thumb


# MAIN DOWNLOADER
@dp.message()
async def downloader(message: Message):

    url = message.text.strip()

    if "instagram.com" not in url:
        await message.reply("❌ Please send a valid Instagram link.")
        return

    status = await message.reply("⏳ Fetching media...")

    try:

        data = await fetch_instagram(url)

        if not data.get("status"):
            await status.edit_text("❌ Failed to fetch media.")
            return

        media_list = data.get("data", [])

        if not media_list:
            await status.edit_text("❌ No media found.")
            return

        await status.edit_text("📥 Downloading...")

        downloaded_files = []

        for media in media_list:

            file_path = await download_file(media["url"])
            downloaded_files.append((file_path, media["type"]))

        await status.edit_text("⬆ Uploading...")

        for file_path, media_type in downloaded_files:

            file = FSInputFile(file_path)

            if media_type == "video":

                thumb = create_thumbnail(file_path)

                await message.answer_video(
                    video=file,
                    thumbnail=FSInputFile(thumb),
                    supports_streaming=True
                )

                if os.path.exists(thumb):
                    os.remove(thumb)

            elif media_type == "image":

                await message.answer_photo(file)

            else:

                await message.answer_document(file)

            if os.path.exists(file_path):
                os.remove(file_path)

        await status.delete()

    except Exception as e:

        await message.reply(f"❌ Error: {e}")


# RUN BOT
async def main():

    print("🚀 Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
