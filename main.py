import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

with open("./token.txt", "r", ) as file:
    token = file.read()

bot = telebot.TeleBot(token)

cards = []
card = {}

def text_unique(key, text):
    '''
    Проверяет, была ли добавлена карточка с таким текстом.
    '''
    global cards
    for card in cards:
        if card[key] == text: 
            return False
        
    return True

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Добро пожаловать!")

# Добавление новой карточки
@bot.message_handler(commands=['newcard'])
def add_new_card(message):
    bot.send_message(message.chat.id, "Введите информацию, которую хотите запомнить")
    bot.register_next_step_handler(message, get_remember_text)

def get_remember_text(message):
    global card 
    if text_unique('remember_text', message.text) == False:
        bot.send_message(message.chat.id, "Карточка с таким текстом уже есть, попробуйте другую")
        bot.register_next_step_handler(message, get_remember_text)
        return 
    card['remember_text'] = message.text
    bot.send_message(message.chat.id, "Введите подсказку, по которой будете вспоминать")
    bot.register_next_step_handler(message, get_hint)

def get_hint(message):
    global cards, card
    if text_unique('hint', message.text) == False:
        bot.send_message(message.chat.id, "Карточка с такой подсказкой уже есть, попробуйте другую")
        bot.register_next_step_handler(message, get_hint)
        return 
    card['hint'] =  message.text
    cards.append(card)
    bot.send_message(message.chat.id, "Карточка для запоминания успешно добавлена!")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.chat.id, message.text)

bot.polling(none_stop=True, interval=0)