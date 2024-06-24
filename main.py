import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types
from datetime import date

import configparser
config = configparser.ConfigParser()
config.read('config.ini')

token = config['token']['value']

bot = telebot.TeleBot(token)

cards = []
card = {"text": str, 
        "hint": str, 
        "mem_level": int,
        "last_study": date}


def text_unique(key, text):
    '''
    Проверяет, была ли добавлена карточка с таким текстом.
    '''
    global cards
    for card in cards:
        if card[key] == text: 
            return False
        
    return True

text1 = "ПОДСКАЗКА"
text2 = "ИНФОРМАЦИЯ ДЛЯ ЗАПОМНИНАНИЯ"

current_text = text1

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Отправляем сообщение с InlineKeyboardMarkup
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Перевернуть карточку", callback_data="change_text")
    markup.add(button)
    bot.send_message(message.chat.id, text1, reply_markup=markup)
    
    # Отправляем сообщение с ReplyKeyboardMarkup
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Не помню')
    button2 = types.KeyboardButton('Помню')
    keyboard.add(button1, button2)

    # Используем send_message для отправки клавиатуры
    bot.send_message(message.chat.id, "Помните ли вы данную карочку?", reply_markup=keyboard)

# Обработчик нажатия на кнопку
@bot.callback_query_handler(func=lambda call: call.data == "change_text")
def callback_change_text(call):
    global current_text
    if current_text == text1: 
        current_text = text2
    else: 
        current_text = text1

    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Перевернуть карточку", callback_data="change_text")
    markup.add(button)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = current_text, reply_markup=markup)
    bot.answer_callback_query(call.id)  # Отвечаем на callback без отправки сообщения

# Добавление новой карточки
@bot.message_handler(commands=['newcard'])
def add_new_card(message):
    bot.send_message(message.chat.id, "Введите информацию, которую хотите запомнить")
    bot.register_next_step_handler(message, get_remember_text)

# Спрашиваем про текст карточки
def get_remember_text(message):
    global card 
    if text_unique('text', message.text) == False:
        bot.send_message(message.chat.id, "Карточка с таким текстом уже есть, попробуйте другую")
        bot.register_next_step_handler(message, get_remember_text)
        return 
    card['text'] = message.text
    bot.send_message(message.chat.id, "Введите подсказку, по которой будете вспоминать")
    bot.register_next_step_handler(message, get_hint)

# Спрашиваем про подсказку для карточки 
def get_hint(message):
    global cards, card
    if text_unique('hint', message.text) == False:
        bot.send_message(message.chat.id, "Карточка с такой подсказкой уже есть, попробуйте другую")
        bot.register_next_step_handler(message, get_hint)
        return 
    card['hint'] =  message.text
    cards.append(card)
    bot.send_message(message.chat.id, "Карточка для запоминания успешно добавлена!")

bot.polling(none_stop=True, interval=0)