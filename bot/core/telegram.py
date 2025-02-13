from telebot import TeleBot

from bot.config import settings

Token = settings.BOT_TOKEN
chat_id = settings.CHAT_ID


def send_message_success(acc, message):
    try:
        str_send = f'✅ Boinker\n<b>Account {acc}  {message}</b>'
        bot = TeleBot(Token)
        bot.send_message(chat_id, str_send, parse_mode='html', disable_notification=True, disable_web_page_preview=True)
    except Exception as error:
        print(error)

def send_message(text):
    str_send = f'<b>{text}</b>'
    bot = TeleBot(Token)
    bot.send_message(chat_id, str_send, parse_mode='html', disable_notification=True, disable_web_page_preview=True)

