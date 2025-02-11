import os
import logging
import requests
import json
import asyncio
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# 🔹 Загружаем переменные окружения из .env
load_dotenv()

# 🔹 Конфигурация API и Telegram бота
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
CLUB_ID = int(os.getenv("CLUB_ID", 1))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_GROUP_ID = int(os.getenv("ALLOWED_GROUP_ID"))  # Разрешённый ID группы

# 🔹 Все UUID ПК в явном виде
PC_UUIDS = {
    1: "03560274-043C-05E0-6906-F30700080009",
    2: "03560274-043C-05E0-6906-B70700080009",
    3: "03560274-043C-05E0-6906-F10700080009",
    4: "03560274-043C-05E0-6906-EF0700080009",
    5: "03560274-043C-05E0-6A06-040700080009",
    6: "03560274-043C-05E0-6A06-140700080009",
    7: "03560274-043C-05E0-6D06-2C0700080009",
    8: "03560274-043C-05E0-6A06-CB0700080009",
    9: "03560274-043C-05E0-6A06-120700080009",
    10: "03560274-043C-05E0-6A06-110700080009",
    11: "03560274-043C-05E0-6C06-D50700080009",
    12: "03560274-043C-05E0-6A06-160700080009",
    13: "03560274-043C-05E0-6A06-950700080009",
    14: "03560274-043C-05E0-6C06-850700080009",
    15: "03560274-043C-05E0-6A06-CC0700080009",
    16: "03560274-043C-05E0-6D06-7D0700080009",
    17: "03560274-043C-05E0-6A06-190700080009",
    18: "03560274-043C-05E0-6906-F20700080009",
    19: "03560274-043C-05E0-6C06-840700080009",
    20: "03560274-043C-05E0-6C06-930700080009",
    21: "03560274-043C-05E0-6906-B50700080009",
    22: "03560274-043C-05E0-6C06-350700080009",
    23: "03560274-043C-05E0-6A06-9D0700080009",
    24: "03560274-043C-05E0-6A06-960700080009",
    25: "03560274-043C-05E0-6A06-940700080009",
    26: "03560274-043C-05E0-6A06-CF0700080009",
    27: "03560274-043C-05E0-6C06-A80700080009",
    28: "03560274-043C-05E0-6A06-130700080009",
    29: "03560274-043C-05E0-6C06-340700080009",
    30: "03560274-043C-05E0-6A06-AD0700080009"
}

# 🔹 Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def switch_to_tech_mode(pc_uuid):
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "club_id": CLUB_ID,
        "command": "tech_start",
        "type": "free",
        "uuids": [pc_uuid]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"🚨 Ошибка соединения с API: {e}")
        return 500, {"message": f"Ошибка соединения с API: {e}"}

# 🔹 Функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    chat_id = update.message.chat_id  
    chat_type = update.message.chat.type  

    if chat_type == "private" or chat_id != ALLOWED_GROUP_ID:
        return  

    if message.startswith("!") and message[1:].startswith("teh") and message[4:].isdigit():
        pc_number = int(message[4:])
        if pc_number in PC_UUIDS:
            pc_uuid = PC_UUIDS[pc_number]
            status_code, response = await switch_to_tech_mode(pc_uuid)

            if status_code == 200 and response.get("status") is True:
                await update.message.reply_text(f"✅ ПК {pc_number} переведён в тех. режим.", quote=False)
            else:
                await update.message.reply_text(f"❌ Ошибка API: {response.get('message', 'Ошибка')}", quote=False)

# 🔹 Функция для отправки напоминания в группу
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    reminder_text = (
        "📢 *Напоминание!*\n"
        "Сегодня в *10:00* администратору провести уборку по плану:\n\n"
        "✅ *Мышки, наушники* – протереть влажными салфетками 🧼\n"
        "✅ *Мониторы* – выключить на 10 минут, затем аккуратно протереть экран специальным средством или салфетками 🖥✨\n"
        "✅ *Клавиатуры* – продуть воздуходувкой над полом 💨⌨\n"
        "✅ *Дверца холодильника* – протереть со средством для стекла 🧴🚪\n"
        "✅ *Джойстики PS5* – обрабатывать после каждого клиента влажными салфетками 🎮🧽\n\n"
        "💡 *Чистота клуба – комфорт для всех!*"
    )
    await context.bot.send_message(chat_id=ALLOWED_GROUP_ID, text=reminder_text, parse_mode="Markdown")

# 🔹 Функция планирования напоминаний
async def schedule_reminders(application: Application):
    now = datetime.datetime.now()
    first_run = now.replace(hour=10, minute=0, second=0, microsecond=0)

    if now > first_run:
        first_run += datetime.timedelta(days=1)

    while first_run.weekday() not in [0, 2, 4]:  
        first_run += datetime.timedelta(days=1)

    delay = (first_run - now).total_seconds()
    logging.info(f"⏳ Первое напоминание через {delay / 3600:.2f} часов")

    await asyncio.sleep(delay)

    while True:
        if datetime.datetime.now().weekday() in [0, 2, 4]:  
            await send_reminder(application.bot)
        await asyncio.sleep(86400)  

# 🔹 Запуск бота
def main():
    logging.info("🚀 Запуск Telegram-бота...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    loop = asyncio.get_event_loop()
    loop.create_task(schedule_reminders(application))  

    application.run_polling()

if __name__ == "__main__":
    main()
