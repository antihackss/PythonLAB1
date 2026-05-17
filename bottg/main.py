# username: ist_24_2_var17_bot

# Импорт необходимых библиотек
import asyncio  # Для асинхронного выполнения операций
import logging  # Для ведения журнала событий (отладка, ошибки)
import random  # Для выбора случайного запасного анекдота
from typing import Optional  # Для указания, что переменная может быть None

import requests  # Для выполнения HTTP-запросов к сайту с анекдотами
from bs4 import BeautifulSoup  # Для парсинга HTML-страниц
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton  # Основные классы Telegram API
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes  # Обработчики событий

TOKEN = "8598601647:AAGEbk1IBXVjgOoknHm1Bcub3bbWM3bit6E"  # Уникальный токен
JOKE_URL = "https://www.anekdot.ru/random/anekdot/"  # Адрес сайта для парсинга анекдотов
REQUEST_TIMEOUT = 15  # Максимальное время ожидания ответа от сайта
PARSING_TIMEOUT = 10  # Таймаут для парсинга одной страницы

# Настройка вывода логов в консоль: время - имя модуля - уровень - сообщение
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # Показываем информационные сообщения и выше (ERROR, WARNING)
)
logger = logging.getLogger(__name__)  # Создаём логгер с именем текущего модуля

# Отключаем излишние предупреждения от библиотеки httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

# Клавиатура
def get_main_keyboard() -> ReplyKeyboardMarkup:
    #Создаёт и возвращает основную клавиатуру с кнопками
    keyboard = [
        [KeyboardButton("😂 Анекдот дня")],  # Первая строка, одна кнопка
        [KeyboardButton("❓ Помощь")],  # Вторая строка, одна кнопка
    ]
    # resize_keyboard=True — подгоняет размер кнопок под содержимое
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Функции для парсинга анедкотов
def _parse_joke_sync() -> Optional[str]:
    # СИНХРОННАЯ функция парсинга анекдота с сайта
    # Выполняется в отдельном потоке, чтобы не блокировать основную работу бота
    #Возвращает:
        # Текст анекдота (строка), если удалось распарсить
        # None, если произошла ошибка
    # Заголовки User-Agent необходимы, чтобы сайт "думал", что к нему обращается браузер,
    # а не бот. Это помогает избежать блокировки.

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        # Отправляем GET-запрос к сайту с анекдотами
        response = requests.get(JOKE_URL, headers=headers, timeout=PARSING_TIMEOUT)
        response.raise_for_status()  # Выбросит исключение, если статус не 200 OK

        # Парсим HTML-код страницы с помощью BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Ищем блок с анекдотом. На сайте anekdot.ru анекдоты могут быть в разных классах
        joke_div = soup.find("div", class_="text") or soup.find("div", class_="anekdot_text")

        if not joke_div:
            logger.warning("Не найден блок с анекдотом на странице")
            return None

        # Извлекаем текст, удаляем лишние пробелы и переносы строк
        joke_text = joke_div.get_text(strip=True)
        joke_text = " ".join(joke_text.split())  # Нормализация пробелов

        # Возвращаем текст только если он длиннее 10 символов (чтобы отсеять мусор)
        return joke_text if len(joke_text) > 10 else None

    # Обрабатываем различные типы ошибок с подробным логированием
    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к сайту анекдотов")
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка соединения с сайтом анекдотов")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка HTTP-запроса: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при парсинге: {e}")

    return None  # При любой ошибке возвращаем None


async def parse_joke_async() -> Optional[str]:
    # Асинхронная обёртка для функции парсинга
    # Запускает синхронную функцию _parse_joke_sync() в отдельном потоке,
    # чтобы не блокировать основной цикл обработки сообщений бота

    loop = asyncio.get_running_loop()  # Получаем текущий цикл событий
    # run_in_executor отправляет задачу в пул потоков
    return await loop.run_in_executor(None, _parse_joke_sync)


def get_fallback_joke() -> str:
    # Возвращает случайный "запасной" анекдот на случай,
    # если не удалось выполнить парсинг сайта
    jokes = [
        "- Почему программисты путают Хэллоуин и Рождество?\n"
        "- Потому что 31 Oct = 25 Dec!",
        "Встречаются два программиста:\n"
        "- Слышал, твоя программа работает?\n"
        "- Работает? Дай боже, чтобы она просто запустилась!",
        "Приходит мужик к ветеринару:\n"
        "- Доктор, моя собака лает по ночам на WiFi-роутер!\n"
        "- Это она ловит Wi-Fi…",
        "- Что делает программист в ванной?\n"
        "- Дебажится…",
    ]
    return random.choice(jokes)  # Случайный выбор

# Обработчики команд и сообщений
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обработчик команды /start
    # Приветствует пользователя по имени и показывает клавиатуру
    user = update.effective_user  # Получаем информацию о пользователе
    # Извлекаем имя: сначала first_name, затем username, иначе "друг"
    user_name = user.first_name or user.username or "друг"

    welcome_text = (
        f"🌟 Привет, {user_name}! 🌟\n\n"
        f"Я бот «Анекдот дня» 🤖\n"
        f"Могу поднять тебе настроение свежим анекдотом!\n\n"
        f"Нажми кнопку «😂 Анекдот дня» или отправь команду /joke"
    )

    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обработчик команды /help
    # Выводит справку по использованию бота
    help_text = (
        "📖 *Справка по боту*\n\n"
        "Доступные команды:\n"
        "/start - начать общение\n"
        "/joke - получить анекдот дня\n"
        "/help - показать эту справку\n\n"
        "Используй кнопки для удобства! 🔘"
    )

    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",  # Поддержка форматирования (жирный шрифт и т.д.)
        reply_markup=get_main_keyboard(),
    )

async def get_joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обработчик команды /joke и нажатия кнопки "Анекдот дня"
    # Отправляет пользователю анекдот, полученный с сайта или запасной
    # Сначала сообщаем, что начался поиск
    await update.message.reply_text("🔍 Ищу свежий анекдот дня... Подожди секундочку!")

    # Пытаемся получить анекдот с сайта
    joke = await parse_joke_async()

    if joke:
        # Успех — отправляем анекдот с сайта
        response_text = f"😂 *Анекдот дня* 😂\n\n{joke}\n\n😄 Хорошего настроения!"
    else:
        # Неудача — используем запасной анекдот
        joke = get_fallback_joke()
        response_text = (
            "😔 Не удалось загрузить анекдот дня с сайта...\n"
            "Но у меня есть запасной вариант:\n\n"
            f"{joke}\n\n"
            "Попробуй позже, возможно, сайт перезагрузится!"
        )

    await update.message.reply_text(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обработчик всех текстовых сообщений (кроме команд)
    # Распознаёт нажатия на кнопки и реагирует на них
    # Если пользователь ввёл что-то произвольное — просит использовать кнопки
    text = update.message.text  # Текст сообщения от пользователя

    if text == "😂 Анекдот дня":
        await get_joke(update, context)
    elif text == "❓ Помощь":
        await help_command(update, context)
    else:
        # Пользователь ввёл что-то с клавиатуры, а не через кнопки
        await update.message.reply_text(
            f"🙁 Я не понимаю команду «{text}».\n"
            "Пожалуйста, используй кнопки или команды:\n"
            "/start, /joke, /help",
            reply_markup=get_main_keyboard(),
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Глобальный обработчик ошибок
    # Логирует ошибку и отправляет пользователю понятное сообщение
    # Это гарантирует, что бот не упадёт при любых обстоятельствах
    logger.error(msg="Исключение при обработке запроса:", exc_info=context.error)

    # Если ошибка произошла в контексте сообщения — уведомляем пользователя
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😔 Произошла небольшая техническая ошибка.\n"
            "Пожалуйста, попробуй еще раз или нажми /start",
            reply_markup=get_main_keyboard(),
        )

# Запуск бота
def main() -> None:
    # Главная функция, запускающая бота
    # Создаёт приложение, регистрирует обработчики и запускает polling
    # Создаём экземпляр приложения с нашим токеном
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("joke", get_joke))

    # Регистрируем обработчик для всех текстовых сообщений (не команд) — кнопки
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    # Регистрируем глобальный обработчик ошибок
    application.add_error_handler(error_handler)

    # Выводим информацию о запуске в консоль и лог
    logger.info("Бот запущен. Username: ist_24_2_var17_bot")
    print("Бот запущен и работает...")
    print("Username: ist_24_2_var17_bot")

    try:
        # Запускаем бота в режиме long polling (постоянно опрашивает сервер Telegram)
        application.run_polling()
    except KeyboardInterrupt:
        # Обработка нажатия Ctrl+C для корректного завершения
        logger.info("Бот остановлен вручную")

# Точка входа в программу
if __name__ == "__main__":
    main()