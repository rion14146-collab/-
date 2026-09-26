import os
import tempfile
from pathlib import Path

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message.document:
        telegram_file = await message.document.get_file()
        filename = message.document.file_name or "file"
        resource_type = "raw"

    elif message.video:
        telegram_file = await message.video.get_file()
        filename = "video.mp4"
        resource_type = "video"

    elif message.photo:
        telegram_file = await message.photo[-1].get_file()
        filename = "image.jpg"
        resource_type = "image"

    elif message.audio:
        telegram_file = await message.audio.get_file()
        filename = message.audio.file_name or "audio.mp3"
        resource_type = "video"

    else:
        await message.reply_text("أرسل صورة أو فيديو أو ملف.")
        return

    await message.reply_text("جاري رفع الملف، انتظر قليلًا...")

    suffix = Path(filename).suffix or ".bin"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp_path = temp.name

    try:
        await telegram_file.download_to_drive(temp_path)

        uploaded = cloudinary.uploader.upload(
            temp_path,
            resource_type=resource_type,
            public_id=f"telegram_files/{Path(filename).stem}",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )

        file_url = uploaded["secure_url"]

        if resource_type in ("image", "video"):
            watch_url = file_url
        else:
            watch_url = "هذا النوع لا يدعم المشاهدة المباشرة"

        download_url = file_url + (
            "?fl_attachment=true"
            if "?" not in file_url
            else "&fl_attachment=true"
        )

        await message.reply_text(
            f"✅ تم رفع الملف\n\n"
            f"🎬 رابط المشاهدة:\n{watch_url}\n\n"
            f"⬇️ رابط التحميل:\n{download_url}"
        )

    except Exception as error:
        print("ERROR:", error)
        await message.reply_text(
            "حدث خطأ أثناء الرفع. تأكد من إعدادات Cloudinary."
        )

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN غير موجود")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.PHOTO
            | filters.VIDEO
            | filters.Document.ALL
            | filters.AUDIO,
            handle_file,
        )
    )

    print("البوت يعمل...")
    app.run_polling()


if __name__ == "__main__":
    main()

