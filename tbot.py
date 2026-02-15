import asyncio
import os
import glob
import uuid
import shutil
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
MAX_MB = 50
DOWNLOAD_ROOT = "downloads"
WORKERS = 2
# ==========================================

VIDEO_EXT = (".mp4", ".mkv", ".mov")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")

os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
queue = asyncio.Queue()


def file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)


async def safe_delete(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        print(f"Error deleting file {path}: {e}")
        pass


async def download_instagram(url, folder):
    # Validate URL to prevent command injection
    if not url.startswith(('http://', 'https://')) or 'instagram.com' not in url:
        raise ValueError("Invalid Instagram URL")
    
    template = f"{folder}/%(id)s_%(index)s.%(ext)s"

    cmd = [
        "yt-dlp",
        "--yes-playlist",
        "--write-info-json",
        "-o", template,
        url
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"yt-dlp failed with error: {stderr.decode()}")


async def send_file(chat_id, path):
    size = file_size_mb(path)
    await bot.send_message(chat_id, f"📦 فایل آماده شد\nحجم واقعی: {size:.2f} MB")

    if size > MAX_MB:
        await bot.send_message(chat_id, "❌ فایل بزرگ‌تر از حد مجاز تلگرام است.")
        await safe_delete(path)
        return

    try:
        if path.lower().endswith(VIDEO_EXT):
            await bot.send_video(chat_id, types.FSInputFile(path))
        elif path.lower().endswith(IMAGE_EXT):
            await bot.send_photo(chat_id, types.FSInputFile(path))
        else:
            await bot.send_document(chat_id, types.FSInputFile(path))
    except Exception as e:
        await bot.send_message(chat_id, f"❌ خطا در ارسال فایل: {str(e)}")
        await safe_delete(path)
    finally:
        await safe_delete(path)


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 لینک پست / ریل / استوری اینستاگرام را ارسال کنید.\n"
        f"حداکثر حجم مجاز: {MAX_MB}MB"
    )


@dp.message()
async def handle_message(message: types.Message):
    if not message.text or "instagram.com" not in message.text:
        return await message.answer("❌ لینک معتبر نیست.")

    await queue.put((message.chat.id, message.text.strip()))
    await message.answer("✅ لینک در صف پردازش قرار گرفت.")


async def worker():
    while True:
        chat_id, url = await queue.get()
        session_id = str(uuid.uuid4())
        folder = os.path.join(DOWNLOAD_ROOT, session_id)
        os.makedirs(folder, exist_ok=True)

        try:
            await bot.send_message(chat_id, "⏳ در حال دانلود...")

            await download_instagram(url, folder)

            files = glob.glob(f"{folder}/*")
            media_files = [
                f for f in files
                if f.lower().endswith(VIDEO_EXT + IMAGE_EXT)
            ]

            if not media_files:
                await bot.send_message(chat_id, "❌ رسانه‌ای پیدا نشد.")
            else:
                for file in sorted(media_files):
                    await send_file(chat_id, file)

        except Exception as e:
            await bot.send_message(chat_id, f"🔥 خطا: {str(e)}")

        finally:
            shutil.rmtree(folder, ignore_errors=True)
            queue.task_done()


async def main():
    for _ in range(WORKERS):
        asyncio.create_task(worker())

    try:
        await dp.start_polling(bot)
    finally:
        # Graceful shutdown
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
