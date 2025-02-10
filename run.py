import os
import requests
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Конфигурация API и бота
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
CLUB_ID = int(os.getenv("CLUB_ID", 0))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = -1002471111192  # ID вашей группы для уведомлений

# Парсим UUID из переменных окружения
def load_pc_uuids():
    uuids = {}
    for key, value in os.environ.items():
        if key.startswith("PC_UUID_"):
            pc_number = int(key.replace("PC_UUID_", ""))
            uuids[pc_number] = value
    return uuids

PC_UUIDS = load_pc_uuids()

# Функция для отправки запроса к API
def switch_to_tech_mode(pc_uuid):
    headers = {
        "X-API-KEY": API_KEY
    }
    payload = {
        "club_id": CLUB_ID,
        "command": "tech_start",
        "type": "free",
        "uuids": pc_uuid
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.status_code, response.json()

# Функция для обработки сообщений
def handle_message(update: Update, context: CallbackContext):
    message = update.message.text.strip()
    user_name = update.message.from_user.full_name
    user_id = update.message.from_user.id

    if message.startswith("teh") and message[3:].isdigit():
        pc_number = int(message[3:])
        if pc_number in PC_UUIDS:
            pc_uuid = PC_UUIDS[pc_number]
            status_code, response = switch_to_tech_mode(pc_uuid)
            if status_code == 200:
                # Уведомление в группу
                notification = (
                    f"👤 **Администратор:** {user_name} (ID: {user_id})\n"
                    f"💻 **Действие:** Перевод ПК {pc_number} в технический режим\n"
                )
                context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=notification, parse_mode="Markdown")

                # Ответ пользователю
                update.message.reply_text(f"✅ ПК {pc_number} (UUID: {pc_uuid}) переведён в технический режим.")
            else:
                update.message.reply_text(f"❌ Ошибка при переводе ПК {pc_number}: {response.get('message', 'Неизвестная ошибка')}")
        else:
            update.message.reply_text(f"❌ ПК с номером {pc_number} не найден в списке.")
    else:
        update.message.reply_text("❌ Неверная команда. Используйте формат: teh<N>, где N — номер ПК.")

# Настройка Telegram-бота
updater = Updater(TELEGRAM_TOKEN)
updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
updater.start_polling()
