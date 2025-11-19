import os
import asyncio
from io import BytesIO
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    filters, ContextTypes
)

from ocr_engine import extract_numbers
from sheets import update_cell

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = "https://your-app-name.up.railway.app/webhook"  # Ganti dengan URL Railway kamu

def next_columns(start_col, count):
    cols = []
    prefix = start_col[:-1]
    suffix = start_col[-1]
    for i in range(count):
        next_suffix = chr(ord(suffix) + i)
        cols.append(f"{prefix}{next_suffix}")
    return cols

def normalize_number(n):
    if isinstance(n, str):
        n = n.replace(",", ".")
    try:
        return float(n)
    except ValueError:
        return n

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Selamat datang! Kirim konfigurasi dalam 5 baris seperti ini:\nNama Sheet\nKolom Awal(ex: EO)\nJumlah Hari\nBaris Real\nBaris ACH"
    )
    context.user_data["state"] = "awaiting_config"

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Sesi selesai. Terima kasih!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")

    if state == "awaiting_config":
        lines = update.message.text.strip().split("\n")
        if len(lines) < 5:
            await update.message.reply_text("Format tidak lengkap. Kirim 5 baris:\nSheet\nKolom Awal\nJumlah Hari\nBaris Real\nBaris ACH")
            return

        try:
            context.user_data["sheet"] = lines[0]
            context.user_data["column_start"] = lines[1].upper()
            context.user_data["day_count"] = int(lines[2])
            context.user_data["row_real"] = int(lines[3])
            context.user_data["row_ach"] = int(lines[4])
            context.user_data["state"] = "ready"
            await update.message.reply_text("Konfigurasi selesai. Silakan kirim gambar KPI.")
        except ValueError:
            await update.message.reply_text("Pastikan jumlah hari dan baris berupa angka.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") != "ready":
        await update.message.reply_text("Silakan kirim perintah /start terlebih dahulu untuk konfigurasi.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()
    image_stream = BytesIO(image_bytes)

    day_count = context.user_data["day_count"]
    min_required = day_count * 2

    raw_numbers = await asyncio.to_thread(extract_numbers, image_stream, min_required)
    numbers = [normalize_number(n) for n in raw_numbers]

    sheet = context.user_data["sheet"]
    column_start = context.user_data["column_start"]
    row_real = context.user_data["row_real"]
    row_ach = context.user_data["row_ach"]

    columns = next_columns(column_start, day_count)

    real_values = numbers[::2]
    ach_values = [round(val * 100, 2) for val in numbers[1::2]]

    for i in range(len(real_values)):
        update_cell(f"{sheet}!{columns[i]}{row_real}", real_values[i])

    for i in range(len(ach_values)):
        update_cell(f"{sheet}!{columns[i]}{row_ach}", ach_values[i])

    await update.message.reply_text(
        f"Data berhasil dikirim ke spreadsheet:\nReal: {real_values}\nACH: {ach_values}\n\nSilakan kirim konfigurasi baru dalam 5 baris:\nSheet\nKolom Awal\nJumlah Hari\nBaris Real\nBaris ACH"
    )
    context.user_data["state"] = "awaiting_config"

# Inisialisasi dan jalankan webhook
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=WEBHOOK_URL
    )