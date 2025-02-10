import os
import logging
import requests
import json
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

    json_payload = json.dumps(payload, ensure_ascii=False)

    logging.info(f"📤 Отправка запроса к API: {API_URL}")
    logging.info(f"🔑 Заголовки: {headers}")

    print("\n=== ОТПРАВЛЕННЫЙ JSON В API ===")
    print(json_payload)
    print("================================\n")

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()

        response_data = response.json()
        response_text = json.dumps(response_data, indent=2, ensure_ascii=False)
        logging.info(f"📩 Статус ответа: {response.status_code}")
        logging.info(f"📊 API ответ (разобранный JSON):\n{response_text}")

        return response.status_code, response_data
    except requests.exceptions.RequestException as e:
        logging.error(f"🚨 Ошибка соединения с API: {e}")
        return 500, {"message": f"Ошибка соединения с API: {e}"}

# 🔹 Функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    chat_id = update.message.chat_id  # ID чата (группы)
    chat_type = update.message.chat.type  # Тип чата (private / group / supergroup)

    # ❌ Игнорируем личные сообщения (ЛС)
    if chat_type == "private":
        logging.warning(f"⚠ Бот получил ЛИЧНОЕ сообщение от {update.message.from_user.full_name}, но не ответил.")
        return  # Выходим без обработки

    # ❌ Игнорируем ВСЕ группы, кроме одной разрешённой
    if chat_id != ALLOWED_GROUP_ID:
        logging.warning(f"⚠ Бот получил сообщение в НЕРАЗРЕШЁННОЙ группе (ID: {chat_id}). Игнорируем.")
        return  # Выходим без обработки

    # 🔹 Проверяем, что сообщение начинается с "teh" и дальше идёт число
    if message.startswith("teh") and message[3:].isdigit():
        pc_number = int(message[3:])
        if pc_number in PC_UUIDS:
            pc_uuid = PC_UUIDS[pc_number]
            logging.info(f"🖥 Перевод ПК {pc_number} (UUID: {pc_uuid}) в тех. режим")

            status_code, response = await switch_to_tech_mode(pc_uuid)

            if status_code == 200 and response.get("status") is True:
                await update.message.reply_text(f"✅ ПК {pc_number} переведён в тех. режим.", quote=False)
            else:
                error_message = response.get("message", "Ошибка API")
                logging.error(f"❌ Ошибка при переводе ПК {pc_number}: {error_message}")
                await update.message.reply_text(f"❌ Ошибка: {error_message}", quote=False)
        else:
            await update.message.reply_text(f"❌ ПК {pc_number} не найден.", quote=False)
    else:
        await update.message.reply_text("❌ Неверная команда. Используйте: `teh<N>`, где `N` — номер ПК.", quote=False)

# 🔹 Запуск бота
def main():
    logging.info("🚀 Запуск Telegram-бота...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
