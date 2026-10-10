import telebot
import dotenv
import os
import json
import subprocess
import sys

dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

with open ("config.json", "r") as f:
    config = json.load(f)

ADMIN_CHAT_ID = config["ADMIN_CHAT_ID"]
PHRAO_CHAT_ID = config["PHRAO_CHAT_ID"]

bot = telebot.TeleBot(BOT_TOKEN)

def get_last_report(reports_dir = "reports") -> str | None:
    files = [
        os.path.join(reports_dir, f)
        for f in os.listdir(reports_dir)
        if f.endswith(".json")
    ]
    if not files:
        return None
    return max(files, key=os.path.getmtime) 


def build_message(report_filename: str) -> str:
    with open(report_filename, "r", encoding="utf-8") as f:
        report = json.load(f)

    top = report.get("top_quote")
    lines = []

    if top:
        lines.append("🏆 Самая популярная цитата:")
        lines.append(top["quote"])
        lines.append(f"— {top['author']} · ❤️ {top['reaction_count']}")
        lines.append("")

    lines.append("✍️ Топ авторов:")
    for a in report["top_authors"]:
        lines.append(f"• {a['author']} — {a['reaction_count']}❤️")

    return "\n".join(lines)


@bot.message_handler(commands=["start"])
def start(message : telebot.types.Message) -> None:
    print(message.chat.id)
    bot.reply_to(message, "Привет! Я бот, который собирает цитаты из канала и формирует ТОП недели.")


@bot.message_handler(commands=["help"])
def help(message: telebot.types.Message) -> None:
    help_text = (
        "Команды:\n"
        "/start - Запустить бота. Важно запустить бота прежде чем делать что - либо еще так как у бота нет возможности инициировать диалог.\n"
        "/report - Собрать и опубликовать ТОП недели. Бот собирает информацию в среднем за 15 секунд. Прошу, не спамьте эту команду.\n"
        "/help - Показать эту помощь."
    )
    bot.reply_to(message, help_text)


@bot.message_handler(commands=["check"])
def check(message : telebot.types.Message) -> None:
    check_text = "Если ты это читаешь, значит @phra0n все настроил и бот полностью рабочий!"
    try:
        bot.send_message(ADMIN_CHAT_ID, check_text)
        print("Сообщение успешно доставлено")
    except Exception as e:
        print(f"Сообщение не доставлено : {e}")

is_running = False

@bot.message_handler(commands=["report"])
def report(message: telebot.types.Message) -> None:
    chat_id = message.chat.id

    global is_running
    if is_running:
        return
    
    is_running = True
    try:
        bot.send_message(chat_id, "Запускаю сбор данных, это займёт немного времени...")

        try:
            result = subprocess.run(
                [sys.executable, "script.py"],
                capture_output=True,
                text=True,
                timeout=60,  
            )
            bot.send_message(chat_id, "Сбор данных завершён.")

        except subprocess.TimeoutExpired:
            bot.send_message(chat_id, "Сбор данных занял слишком много времени. Прервано.")
            return

        if result.returncode != 0:
            bot.send_message(chat_id, f"Юзербот упал с ошибкой:\n{result.stderr}")
            return

        last_report_file = get_last_report()
        if last_report_file is None:
            bot.send_message(chat_id, "Отчётов нет, хотя юзербот завершился успешно. Странно.")
            return

        report_text = build_message(last_report_file)

        bot.send_message(chat_id, "Отчёт готов:")
        bot.send_message(chat_id, report_text)

        try:
            bot.send_message(ADMIN_CHAT_ID, report_text)
            bot.send_message(chat_id, f"Опубликовано в {ADMIN_CHAT_ID}.")
        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(chat_id, f"Не удалось опубликовать: {e.description}")
    finally:
        is_running = False


@bot.message_handler(commands=["phrao_report"])
def phrao_report(message: telebot.types.Message) -> None:
    global is_running
    if is_running:
        return
    
    is_running = True
    try:
        try:
            result = subprocess.run(
                [sys.executable, "script.py"],
                capture_output=True,
                text=True,
                timeout=60,  
            )
            bot.send_message(PHRAO_CHAT_ID, "Сбор данных завершён.")

        except subprocess.TimeoutExpired:
            bot.send_message(PHRAO_CHAT_ID, "Сбор данных занял слишком много времени. Прервано.")
            return

        if result.returncode != 0:
            bot.send_message(PHRAO_CHAT_ID, f"Юзербот упал с ошибкой:\n{result.stderr}")
            return

        last_report_file = get_last_report()
        if last_report_file is None:
            bot.send_message(PHRAO_CHAT_ID, "Отчётов нет, хотя юзербот завершился успешно. Странно.")
            return

        report_text = build_message(last_report_file)

        try:
            bot.send_message(PHRAO_CHAT_ID, report_text)
            bot.send_message(PHRAO_CHAT_ID, f"Опубликовано в {PHRAO_CHAT_ID}.")
        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(PHRAO_CHAT_ID, f"Не удалось опубликовать: {e.description}")
    finally:
        is_running = False

bot.set_my_commands([
    telebot.types.BotCommand("start", "Запустить бота"),
    telebot.types.BotCommand("report", "Собрать и опубликовать ТОП недели"),
    telebot.types.BotCommand("help", "Показать помощь"),
])


bot.delete_webhook(drop_pending_updates=True)
print("Бот запущен. Ожидание команд...")
bot.infinity_polling()

