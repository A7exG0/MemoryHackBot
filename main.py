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

text1 = "ПОДСКАЗКА"
text2 = "ИНФОРМАЦИЯ ДЛЯ ЗАПОМНИНАНИЯ"
connection = object

current_text = text1

def show_card(message, card):
    bot.send_message(message.chat.id, f"id: {card[0]}\n---------------------------\n{card[2]}\n---------------------------\n{card[1]}")


# Команда /home
@bot.message_handler(commands=['home'])
def send_home(message):
    bot.send_message(message.chat.id, "Вы на главной странице.")

# Команда /change
@bot.message_handler(commands=['change'])
def ask_id_for_change(message):    
    bot.send_message(message.chat.id, "Введите id карточки")
    bot.register_next_step_handler(message, get_card_to_change)

def get_card_to_change(message):
    print("Получаем карточку")
    id = message.text
    card = db.select_by_value(connection, "card_id", id)
    if not card: 
        print(f"Карточки с {id} нет")
        bot.send_message(message.chat.id, "Карточки с таким id нет")
        return
    else:
        show_card(message, card)
        choose_column_to_change(message, id)

def choose_column_to_change(message, id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Подсказка')
    button2 = types.KeyboardButton('Текст')
    keyboard.add(button1, button2)

    bot.send_message(message.chat.id, "Выберите параметр, по которому будем менять карточку", reply_markup=keyboard)
    bot.register_next_step_handler(message, lambda msg: check_column(msg, keyboard, id))

def check_column(message, keyboard, id):
    column = message.text
    if column == "Подсказка":
        print("Выбрано изменение по подсказке")
        column = "hint"
    elif column == "Текст":
        print("Выбрано изменение по тексту")
        column = "text"
    else:
        bot.send_message(message.chat.id, "Есть два варианта. Попробуйте еще", reply_markup=keyboard)
        bot.register_next_step_handler(message, lambda msg: check_column(msg, keyboard, id))
        return 

    hide_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Введите новое значение", reply_markup=hide_keyboard)
    bot.register_next_step_handler(message, lambda msg: change_card(msg, column, id))

def change_card(message, column, id):
    if db.change_card(connection, id, column, message.text):
        print("Изменение прошло успешно")
        bot.send_message(message.chat.id, "Карточка изменена:")
        card = db.select_by_value(connection, "card_id", id)
        show_card(message, card)
    else:
        print("Ошибка в функции change_card")
        bot.send_message(message.chat.id, "Произошла ошибка при изменении карточки(")

        
# Команда /delete
@bot.message_handler(commands=['delete'])
def ask_id_for_delete(message):    
    bot.send_message(message.chat.id, "Введите id карточки")
    bot.register_next_step_handler(message, delete_card)

def delete_card(message):
    print("Начинаем удалять карточку")
    id = message.text
    is_unique = db.value_unique(connection, "cards", "card_id", id)
    if is_unique: 
        print(f"Карточки с {id} нет")
        bot.send_message(message.chat.id, "Карточки с таким id нет")
        return
    elif not is_unique:
        if db.delete_card(connection, id): 
            print(f"Карточка удалена")
            bot.send_message(message.chat.id, "Карточка удалена")
        else:
            print(f"Произошла ошибка при удалении")
            bot.send_message(message.chat.id, "Произошла ошибка при удалении(")
    else:
        print(f"Произошла ошибка при в функции value_unique")
        bot.send_message(message.chat.id, "Произошла ошибка при удалении(")
            

# Команда /showall для отображения всех карточек
@bot.message_handler(commands=['showall'])
def show_all(message):
    global connection
    print('Получаем карточки из базы данных')
    bot.send_message(message.chat.id, "Выводим все карточки")
    cards = db.select_all_cards(connection)
    if cards is False:
        bot.send_message(message.chat.id, "Произошла ошибка")
        return
    print("Карточки успешно получены")
    for card in cards: 
        show_card(message, card)        

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def udentify_user(message):
    global connection 

    user_id = message.chat.id
    bot.send_message(message.chat.id, "Доброго времени суток.\nЕсли хотите начать учиться, введите команду /learn\nХотите добавить новую карточку, введите команду /newcard\nХотите увидеть все карточки, введите команду /showall\nХотите найти карточку, введите команду /find")

    connection = db.connect_database()
    is_unique = db.value_unique(connection, "users", "user_id", user_id)
    if is_unique is True: 
        print("Новый пользователь")
        if db.sql_insert(connection, "users", user_id=user_id) is False:
            bot.send_message(message.chat.id, "Произошла ошибка при знакомстве с пользователем(")
    elif is_unique is False:
        print("Знакомый пользователь")
    else: 
        bot.send_message(message.chat.id, "Произошла ошибка при знакомстве с пользователем(")
    
# Обработчик команды /find
@bot.message_handler(commands=['find'])
def choose_parameter(message):
    # Отправляем сообщение с ReplyKeyboardMarkup
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('id')
    button2 = types.KeyboardButton('Подсказка')
    button3 = types.KeyboardButton('Текст')
    keyboard.add(button1, button2, button3)

    bot.send_message(message.chat.id, "Выберите параметр, по которому будем искать карточку", reply_markup=keyboard)
    bot.register_next_step_handler(message, lambda msg: check_find_param(msg, keyboard))

def check_find_param(message, keyboard):
    param = message.text
    column = ""
    if param == "id":
        print("Выбран поиск по id")
        column = "card_id"
    elif param == "Подсказка":
        print("Выбран поиск по подсказке")
        column = "hint"
    elif param == "Текст":
        print("Выбран поиск по тексту")
        column = "text"
    else:
        bot.send_message(message.chat.id, "Есть только три варианта. Попробуйте еще", reply_markup=keyboard)
        bot.register_next_step_handler(message, lambda msg: check_find_param(msg, keyboard))

    hide_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Введите значение для поиска", reply_markup=hide_keyboard)
    bot.register_next_step_handler(message, lambda msg: find_card(msg, column))

def find_card(message, column):
    print("Начинаем поиск в базе данных")
    card = db.select_by_value(connection, column, message.text)
    if not card:
        bot.send_message(message.chat.id, "Такой карточки нет")
        print(f"Карточка со значение \"{message.text}\" в колонке {column} не найдена")
    else:
        show_card(message, card)
        print("Карточка найдена")


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

    is_unique = db.value_unique(connection, "cards", "text", text)
    if is_unique == -1:         
        bot.send_message(message.chat.id, "Произошла ошибка(")
        return
    
    if not is_unique:
        bot.send_message(message.chat.id, "Карточка с таким текстом уже есть, попробуйте другой")
        bot.register_next_step_handler(message, get_remember_text)
        return
    bot.send_message(message.chat.id, "Введите подсказку, по которой будете вспоминать")
    bot.register_next_step_handler(message, lambda msg: get_hint(msg, text))

# Спрашиваем про подсказку для карточки 
def get_hint(message, text):
    global connection

    if not db.value_unique(connection, "cards", "hint", message.text):
        bot.send_message(message.chat.id, "Карточка с такой подсказкой уже есть, попробуйте другую")
        bot.register_next_step_handler(message, lambda msg: get_hint(msg, text))
        return

    if db.sql_insert(connection=connection, table="cards", text=text, hint=message.text, user_id=message.chat.id) is False: 
        bot.send_message(message.chat.id, "Произошла ошибка. Карточка не добавлена(")
        print("Произошла ошибка при добавлении карточки")
        return 
    
    print("Карточка сделана и занесена в базу данных")
    bot.send_message(message.chat.id, "Карточка для запоминания успешно добавлена!")

bot.polling(none_stop=True, interval=0)