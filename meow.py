import logging
import openai
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import OPENROUTER_API_KEY

# Инициализация клиента OpenRouter
from openai import OpenAI
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,  # Убедись, что ключ не пустой!
    default_headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
)
# Словарь для хранения прогресса пользователей
user_progress = {}

# Функция для создания клавиатуры
def get_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("Получить новый кейс", callback_data="get_case")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reply_keyboard():
    keyboard = [["Показать прогресс", "Оплатить доступ"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_progress[user_id] = {"cases_solved": 0, "last_case": None}

    logging.info("Отправка приветственного сообщения с выпадающим меню.")
    await update.message.reply_text(
        "Привет, я BTrainer. Я помогаю КПТ-психотерапевтам улучшать свои профессиональные навыки."
        " Используй команду /case для получения нового кейса.",
        reply_markup=get_reply_keyboard()  # Добавляем выпадающее меню
    )

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logging.info(f"Нажата кнопка: {query.data}")
    await query.answer()

    if query.data == "get_case":
        await get_case(update, context)

# Функция для генерации терапевтического кейса
def generate_case():
    try:
        prompt = ("Ты — помощник для студентов-психологов, который генерирует кейсы для практики, дает обратную связь, подмечая плюсы и минусы решения, и рекомендации по его улучшению. "
        "Напиши пользователю короткий терапевтический кейс на основе информации из книги Когнитивно-поведенческая терапия. От основ к направлениям. Джудит Бек. 3-е издание 2024 г. и ожидай решения пользователя. Формат кейса: Название. Описание."
        "Не используй форматирование (**, [], и т.д.).")
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",  # Модель которую будете использовать
            messages=[{"role": "user", "content": prompt}]
        )
        if completion and hasattr(completion, 'choices') and completion.choices:
            content = completion.choices[0].message.content
            cleaned_content = re.sub(r'<.*?>', '', content).strip()  # Убираем теги
            return cleaned_content
        else:
            return "Не удалось сгенерировать кейс."
    except Exception as e:
        logging.error(f"Ошибка при генерации кейса: {e}")
        return "Произошла ошибка при генерации кейса."

# Команда /case для получения нового кейса
async def get_case(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_progress:
        user_progress[user_id] = {"cases_solved": 0, "last_case": None}

    case = generate_case()
    user_progress[user_id]["last_case"] = case

    if update.callback_query:  # Если вызвано через кнопку
        await update.callback_query.edit_message_text(
            f"Ваш новый терапевтический кейс:\n\n{case}\n\nВведите ваше решение.",
            reply_markup=get_inline_keyboard()  # Добавляем inline-кнопку
        )
    else:  # Если вызвано через команду
        await update.message.reply_text(
            f"Ваш новый терапевтический кейс:\n\n{case}\n\nВведите ваше решение.",
            reply_markup=get_inline_keyboard()  # Добавляем inline-кнопку
        )
# Анализ решения с помощью OpenRouter
def analyze_solution(case, solution):
    try:
        prompt = f"Кейс: {case}\nРешение: {solution}\nПроанализируй решение, напиши его плюсы и минусы и дай рекомендации."
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",  # Модель которую будете использовать
            messages=[{"role": "user", "content": prompt}]
        )
        if completion and hasattr(completion, 'choices') and completion.choices:
            content = completion.choices[0].message.content
            cleaned_content = re.sub(r'<.*?>', '', content).strip()  # Убираем теги
            return cleaned_content
        else:
            return "Не удалось проанализировать решение."
    except Exception as e:
        logging.error(f"Ошибка при анализе решения: {e}")
        return "Произошла ошибка при анализе решения."

# Обработка решения пользователя
async def handle_solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_solution = update.message.text
    last_case = user_progress.get(user_id, {}).get("last_case")

    if not last_case:
        await update.message.reply_text(
            "Сначала получите кейс с помощью команды /case.",
            reply_markup=get_reply_keyboard()  # Добавляем выпадающее меню
        )
        return

    analysis = analyze_solution(last_case, user_solution)
    user_progress[user_id]["cases_solved"] += 1

    await update.message.reply_text(
        f"Анализ вашего решения:\n\n{analysis}",
        reply_markup=get_inline_keyboard()  # Добавляем inline-кнопку
    )
# Команда /progress для отображения прогресса
async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    progress = user_progress.get(user_id, {"cases_solved": 0})

    await update.message.reply_text(
        f"Вы решили {progress['cases_solved']} кейсов.",
        reply_markup=get_reply_keyboard()  # Добавляем выпадающее меню
    )
# Команда /pay для оплаты доступа
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment_url = "https://your-payment-link.com"  # Замените на реальную ссылку для оплаты

    await update.message.reply_text(
        f"Для получения расширенного доступа перейдите по ссылке: {payment_url}",
        reply_markup=get_reply_keyboard()  # Добавляем выпадающее меню
    )
# Основная функция
def main():
    """Основная функция для запуска бота."""
    # Включение логирования для отслеживания ошибок
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    TELEGRAM_TOKEN = '7751645048:AAFyXjFFWHM8SDtLV0MVCwNVTu6LPqfSZBE'

    # Инициализация приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("case", get_case))
    application.add_handler(CommandHandler("progress", show_progress))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_solution))
    application.add_handler(CallbackQueryHandler(button_handler))  # Добавляем обработчик кнопок

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
