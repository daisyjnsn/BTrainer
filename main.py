from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import requests
from requests.auth import HTTPBasicAuth


# Настройки логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(name)

# Ваши данные ЮKassa
SHOP_ID = 'ВАШ_ИДЕНТИФИКАТ_МАГАЗИНА'
SECRET_KEY = 'ВАШ_СЕКРЕТНЫЙ_КЛЮЧ'

# Функция генерации терапевтического кейса
def generate_case():
    # Здесь вы можете добавить логику для генерации кейсов
    return "Пример терапевтического кейса: Пациент испытывает тревогу при общении."

# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! Я BTrainer, ваш виртуальный помощник. "
        "Команды: /case - получить терапевтический кейс, /pay - оплатить доступ к дополнительным функциям.",
        reply_markup=ForceReply(selective=True),
    )

# Функция получения кейса
async def case(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    case_text = generate_case()
    await update.message.reply_text(case_text)

# Функция оплаты
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    amount = 100.00  # Сумма в рублях
    payment_data = {
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://ваш-сайт.ру/return"
        },
        "capture": True,
        "description": "Оплата за доступ к дополнительным функциям BTrainer"
    }

    try:
        # Ensure the credentials are passed as plain strings
        response = requests.post(
            'https://api.yookassa.ru/v3/payments',
            json=payment_data,
            auth=HTTPBasicAuth(SHOP_ID, SECRET_KEY)
        )
        response.raise_for_status()
        payment = response.json()
        payment_url = payment['confirmation']['confirmation_url']
        await update.message.reply_text(f"Перейдите по ссылке для оплаты: {payment_url}")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        await update.message.reply_text("Ошибка при создании платежа. Пожалуйста, проверьте свои учетные данные и попробуйте снова.")
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Основная функция
def main() -> None:
    # Вставьте ваш токен
    application = ApplicationBuilder().token("7521673360:AAFAjbx3fHud3M85BBrksZFsJ2E9gwi-zeo").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("case", case))
    application.add_handler(CommandHandler("pay", pay))

    # Запуск бота
    application.run_polling()

if name == 'main':
    main()