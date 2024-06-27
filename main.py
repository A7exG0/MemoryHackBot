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

connection = object


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

    connection = db.connect_database()
    user_id = message.chat.id
    bot.send_message(message.chat.id, "Доброго времени суток.\nЕсли хотите начать учиться, введите команду /learn\nХотите добавить новую карточку, введите команду /newcard\nХотите увидеть все карточки, введите команду /showall\nХотите найти карточку, введите команду /find")

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
        return

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


class Cards(): 
    def __init__(self, cards):
        self.cards = []
        for card in cards:
            self.add_card(card)
        self.current = 0 # Отображает номер текущей карты 
        self.number_learned = 0 # Фиксирует количество выученных карточке
        self.index_last_card = 0 # Будет указывать на последнюю полученную карту 

    def add_card(self, card):
        card = {
            "card_id": card[0],
            "text": card[1],
            "hint": card[2],
            "repetitions_number": "0"
        }
        self.cards.append(card)

    def __next__(self):
        # Если дашли до конца колоды, то обнуляем счетчики
        if self.current == len(self.cards):
            self.current = 0
            self.number_learned = 0

        # Цикл пропуска выученных карточек
        while(self.number_learned < len(self.cards)):
            card =  self.cards[self.current]
            if card["repetitions_number"] == 3: 
                self.number_learned += 1
                if self.number_learned == len(self.cards):
                    break
            else:
                self.index_last_card = self.current
                self.current += 1
                return card
            
            self.current += 1
            # Обнуляем значения, если дошли до конца карточек
            if self.current == len(self.cards):
                self.current = 0
                self.number_learned = 0
        
        # Если все карточки выучены, то возвратим это
        return "Learned everything"
    
    def change_last_card(self):
        current_repetitions_number = self.cards[self.index_last_card]["repetitions_number"]
        self.cards[self.index_last_card]["repetitions_number"] = int(current_repetitions_number) + 1
    
    def get_last_card(self):
        return self.cards[self.index_last_card]
        
current_text = hint_text = remember_text = ""
cards : Cards

# Обработчик команды /learn
@bot.message_handler(commands=['learn'])
def get_new_cards(message):
    global connection, cards

    # Отправляем сообщение с ReplyKeyboardMarkup
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Не помню')
    button2 = types.KeyboardButton('Помню')
    keyboard.add(button1, button2)

    bot.send_message(message.chat.id, text = "Сейчас вам будет показана карточка. Ваша задача вспомнить текст карточки по подсказке и ответить получилось ли у вас это или нет.",  reply_markup=keyboard)   

    # Выбираем все новые карточки 
    cards_to_study = db.select_where_condition(connection, "memlevel = 0")
    cards = Cards(cards_to_study)
    
    show_next_card(message, keyboard)


def show_next_card(message, keyboard):
    global hint_text, remember_text, current_text, cards
    card = next(cards)
    if card == "Learned everything":
        hide_keyboard = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Отлично! Вы запомнили все карточки, следующее повторение будет завтра в 20:00. Не опаздывайте!", reply_markup=hide_keyboard)
        return
    
    hint_text = card["hint"]
    current_text = remember_text = card["text"]

     # Отправляем сообщение с InlineKeyboardMarkup
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Перевернуть карточку", callback_data="change_text")
    markup.add(button)
    message_for_ban = bot.send_message(message.chat.id, text = hint_text, reply_markup=markup)

    bot.register_next_step_handler(message, lambda msg: check_answer(msg, keyboard, message_for_ban))

def check_answer(message, keyboard, message_for_ban):
    global cards, current_text

    answer = message.text
    if answer == "Помню":
        cards.change_last_card() # увеличиеваем repetitions_number
    elif answer == "Не помню":
        bot.send_message(message.chat.id, "Запомните карточку получше. Мы к ней еще вернемся. Следующая карточка:")
    else:
        bot.send_message(message.chat.id, "Есть только два варианта. Попробуйте еще раз", reply_markup=keyboard)
        bot.register_next_step_handler(message, lambda msg: check_answer(msg, keyboard, message_for_ban))
        return
    
    card = cards.get_last_card()
    text = f"id: {card['card_id']}\n---------------------------\n{card['hint']}\n---------------------------\n{card['text']}\n---------------------------\nСколько раз осталось повторить: {3 - int(card["repetitions_number"])}"
    bot.edit_message_text(chat_id=message_for_ban.chat.id, message_id=message_for_ban.message_id, text=text)
    # Переходим к следующей карточке
    show_next_card(message, keyboard)


# Обработчик нажатия на кнопку
@bot.callback_query_handler(func=lambda call: call.data == "change_text")
def callback_change_text(call):
    global current_text, hint_text, remember_text, cards
    
    # Проверка на изменение текста перед обновлением
    if call.message.text != current_text:
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text="Перевернуть карточку", callback_data="change_text")
        markup.add(button)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=current_text, reply_markup=markup)
    
    if current_text == hint_text: 
        current_text = remember_text
    else: 
        current_text = hint_text

    bot.answer_callback_query(call.id)  # Отвечаем на callback без отправки сообщения
    print("Карточка перевернута")

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