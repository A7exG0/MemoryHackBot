import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types
from datetime import date

import db 

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
connection = object

current_text = text1

# Команда /home
@bot.message_handler(commands=['home'])
def send_home(message):
    bot.send_message(message.chat.id, "Вы на главной странице.")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def udentify_user(message):
    global connection 

    user_id = message.chat.id
    bot.send_message(message.chat.id, "Доброго времени суток. Если хотите начать учиться, введите команду /learn.\nХотите добавить новую карточку, введите команду /newcard")

    connection = db.connect_database()
    if db.user_exist(connection, user_id) is False: # если пользователя не существует, то создаем новую запись в базе данных 
        print("Новый пользователь")
        db.add_user(connection, user_id)
    else:
        print("Знакомый пользователь")
    

# Обработчик команды /learn
@bot.message_handler(commands=['learn'])
def learn_cards(message):
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
    global connection 
    text = message.text
    if db.data_unique(connection, "text", text) is False:
        bot.send_message(message.chat.id, "Карточка с таким текстом уже есть, попробуйте другой")
        bot.register_next_step_handler(message, get_remember_text)
        return
    bot.send_message(message.chat.id, "Введите подсказку, по которой будете вспоминать")
    bot.register_next_step_handler(message, lambda msg: get_hint(msg, text))

# Спрашиваем про подсказку для карточки 
def get_hint(message, text):
    global connection

    if db.data_unique(connection, "hint", message.text) is False:
        bot.send_message(message.chat.id, "Карточка с такой подсказкой уже есть, попробуйте другую")
        bot.register_next_step_handler(message, lambda msg: get_hint(msg, text))
        return

    if db.add_card(connection=connection, text=text, hint=message.text, user_id=message.chat.id) is False: 
        bot.send_message(message.chat.id, "Произошла ошибка. Карточка не добавлена(")
        print("Произошла ошибка при добавлении карточки")
        return 
    
    print("Карточка сделана и занесена в базу данных")
    bot.send_message(message.chat.id, "Карточка для запоминания успешно добавлена!")

bot.polling(none_stop=True, interval=0)