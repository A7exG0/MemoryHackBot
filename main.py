from telebot import types
import db 
from datetime import datetime, timedelta
from bot_logging import logger
from bb import bot
import bb


STUDY_TIME = "00:00"
line_str = "---------------"

class Card():
    '''
    Класс для удобной работы с параметрами карточки.
    '''
    def __init__(self, card, repetitions_number):
        self.card_id = card[0]
        self.text = card[1]
        self.hint = card[2]
        self.memlevel = int(card[3])
        self.repetitions_number = repetitions_number
        self.nextstudy = None
    
    def get_info(self):
        '''
        Возвращает информацию о карточке.
        '''
        text = f"id: {self.card_id}\n{line_str}\n{self.hint}\n{line_str}\n{self.text}\n{line_str}\n"
        if self.repetitions_number == 0:
            return text + "Супер! Карточка в памяти"
        else:
            return text + f"Осталось повторить {self.repetitions_number} раз"
        
    def reduce_memlevel(self):
        '''
        Уменьшает значение memelevel.
        '''
        if self.memlevel > 0: 
            self.memlevel -= 1

class Cards(): 
    '''
    Класс-итераратор для удобной работы с набором карточек. 
    '''
    def __init__(self):
        self.cards_array = []    # Массив всех карточек
        self.current = 0         # Отображает номер текущей карты 
        self.number_learned = 0  # Фиксирует количество выученных карточке
        self.index_last_card = 0 # Будет указывать на последнюю полученную карту 

    def add_card(self, card, repetitions_number=1):
        '''
        Добовляет карточку в основной массив 
        '''
        card = Card(card, repetitions_number)
        self.cards_array.append(card)

    def __len__(self):
        return len(self.cards_array)

    def __next__(self):
        '''
        Получение следующей карточки
        '''
        # Если дашли до конца колоды, то обнуляем счетчики
        if self.current == len(self.cards_array):
            self.current = 0
            self.number_learned = 0

        # Цикл пропуска выученных карточек
        while(self.number_learned < len(self.cards_array)):
            card = self.cards_array[self.current]
            if card.repetitions_number == 0: # если повторять карточку не нужно, значит ее мы выучили
                self.number_learned += 1
                if self.number_learned == len(self.cards_array): # если выучили все карточки - выходим из цикла
                    break
            else:
                self.index_last_card = self.current
                self.current += 1
                return card
            
            self.current += 1
            # Обнуляем значения, если дошли до конца карточек
            if self.current == len(self.cards_array):
                self.current = 0
                self.number_learned = 0
        
        # Если все карточки выучены, то возвратим это
        return "Learned everything"
    
    def reduce_card_repetition(self):
        '''
        Уменьшает количество повторений.
        '''
        self.cards_array[self.index_last_card].repetitions_number -= 1
    
    def reduce_card_memlevel(self):
        '''
        Уменьшает memlevel карточки
        '''
        self.cards_array[self.index_last_card].reduce_memlevel()

    def get_last_card(self):
        '''
        Получаем последнюю полученную карточку.
        '''
        return self.cards_array[self.index_last_card]
    
    def exists(self):
        '''
        Метод проверяет, есть ли вообще карточки.
        '''
        return self.cards_array
    
    def reduce_number_of_cards(self, new_number):
        '''
        Функция, которая будет сокращать количество карт для изучения, чтобы не пришлось за раз учить 100 карточек
        '''
        if len(self.cards_array) > new_number: 
            self.cards_array = self.cards_array[:new_number]
        

current_text = hint_text = remember_text = ""
cards : Cards

def get_date_in_x_days(x : int):
    '''
    Функция получает x и возвращает дату через x дней. 
    '''
    today = datetime.now()
    nextdate = today + timedelta(days=x)
    # Возвращаем завтрашнюю дату в формате YYYY-MM-DD hh:mm
    return nextdate.strftime("%Y-%m-%d") + " " + STUDY_TIME


def get_nextstudy_days(memlevel: int):
    '''
    Функция определяет следующую дату для повторения исходя из значения memlevel. 
    Интервал между повторениями это 2^(memlevel - 1) дней.
    Пример:
    1-ое повторение будет на следующий день. 2-ое - послезавтра. 3-ое - через 4 дня и т.д.
    '''
    return 2 ** memlevel


def show_card(message, card, show_date = False):
    '''
    Функция отображает информацию карточки. Флаг show_date определяет будет ли отображена дата следующего обучения.
    '''
    if show_date: 
        bot.send_message(message.chat.id, f"id: {card[0]}\nmemlevel: {card[3]}\n{line_str}\n{card[2]}\n{line_str}\n{card[1]}\n{line_str}\nСледующее повторение: {card[4]}")
    else:
        bot.send_message(message.chat.id, f"id: {card[0]}\nmemlevel: {card[3]}\n{line_str}\n{card[2]}\n{line_str}\n{card[1]}")

def get_cards_from_db():
    '''
    Функция получения карточек из базы данных для изучения 
    '''
    cards = Cards()
    # Выбираем все карточки, которые созрели для повторения
    today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cards_to_repetition = db.select_where_condition(f"memlevel > 0 and '{today_date}' > nextstudy")
   
    if cards_to_repetition:
        for card in cards_to_repetition:
            cards.add_card(card, repetitions_number=1) # карточки для повторения нужно повторить только один раз 

    # Выбираем все новые карточки 
    cards_to_study = db.select_where_condition(f"memlevel = 0")
    if cards_to_study:
        for card in cards_to_study:
            cards.add_card(card, repetitions_number=3) # Новые карточки повторить нужно будет три раза

    if not cards.exists(): 
        return []
    else:
        return cards

# Команда /cancel
def check_cancel(message):
    '''
    Функция проверяет, ввел ли пользователь комманду /cancel
    '''
    if message.text == "/cancel":
        logger.info("Вызвана команда /cancel")
        bot.send_message(message.chat.id, "Вы на главном экране")
        return True
    else: 
        return False


# Команда /changegroup
@bot.message_handler(commands=['changegroup'])
def change_group(message):    
    '''
    1 функция команды /changegroup
    '''
    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return 
    
    logger.info("Вызвана команда /changegroup")
    bot.send_message(message.chat.id, "Введите название группы")
    bot.register_next_step_handler(message, get_group_name)

def get_group_name(message):
    '''
    2 функция команды /changegroup.
    '''
    if check_cancel(message):
        return
    
    group = message.text
    bot.send_message(message.chat.id, f"Группа изменена на {group}")
    bb.group = group
    logger.info("Команда /changegroup отработала успешно")

# Команда /groups
@bot.message_handler(commands=['groups'])
def show_all_groups(message):
    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return 
    
    logger.info("Вызвана команда /groups")

    groups = db.select_all_groups()
    str_message = ''
    for index in groups: 
        str_message += index[0] + "\n"
    
    str_message += f"Текущая группа: {bb.group}"
    bot.send_message(message.chat.id, str_message)
    logger.info("Команда /groups успешно отработала")


# Команда /change
@bot.message_handler(commands=['change'])
def ask_id_for_change(message):    
    '''
    1 функция команды /change.
    Ввод id карточки для изменения
    '''
    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return 
    
    logger.info("Вызвана команда /change")
    bot.send_message(message.chat.id, "Введите id карточки")
    bot.register_next_step_handler(message, get_card_to_change)

def get_card_to_change(message):
    '''
    2 функция команды /change.
    Находит карточку по id.
    '''
    if check_cancel(message):
        return
    
    id = message.text

    card = db.select_by_value("card_id", id,)
    if not card: 
        bot.send_message(message.chat.id, "Карточки с таким id нет")
        return
    else:
        show_card(message, card)
        choose_column_to_change(message, id)

def choose_column_to_change(message, id):
    '''
    3 функция команды /change.
    Выбор параметра для изменения.
    '''
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Подсказка')
    button2 = types.KeyboardButton('Текст')
    keyboard.add(button1, button2)

    bot.send_message(message.chat.id, "Выберите параметр, по которому будем менять карточку", reply_markup=keyboard)
    bot.register_next_step_handler(message, lambda msg: check_column(msg, keyboard, id))

def check_column(message, keyboard, id):
    '''
    4 функция команды /change. 
    Проверка корректности выбора параметра изменения.
    '''
    if check_cancel(message):
        return
    
    column = message.text
    if column == "Подсказка":
        column = "hint"
    elif column == "Текст":
        column = "text"
    else:
        bot.send_message(message.chat.id, "Есть два варианта. Попробуйте еще", reply_markup=keyboard)
        bot.register_next_step_handler(message, lambda msg: check_column(msg, keyboard, id))
        return 

    hide_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Введите новое значение", reply_markup=hide_keyboard)
    bot.register_next_step_handler(message, lambda msg: change_card(msg, column, id))

def change_card(message, column, id):
    '''
    5 функция команды /change. 
    Изменение карточки.
    '''
    if db.change_card(id, column, message.text):
        logger.info("Команда /change отрабтала успешно")
        bot.send_message(message.chat.id, "Карточка изменена:")
        card = db.select_by_value("card_id", id)
        show_card(message, card)
    else:
        logger.error("В команде /change произошла ошибка")
        bot.send_message(message.chat.id, "Произошла ошибка при изменении карточки(")

        
# Команда /delete
@bot.message_handler(commands=['delete'])
def ask_id_for_delete(message):    
    '''
    1 функция команды /delete.
    Ввод id карточки для удаления.
    '''
    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return
    
    logger.info("Вызвана команда /delete")
    bot.send_message(message.chat.id, "Введите id карточки")
    bot.register_next_step_handler(message, delete_card)

def delete_card(message):
    '''
    2 функция команды /delete.
    Удаляет карточку.
    '''
    if check_cancel(message):
        return

    id = message.text

    is_unique = db.value_unique("cards", "card_id", id)
    if is_unique: 
        bot.send_message(message.chat.id, "Карточки с таким id нет")
        return
    elif not is_unique:
        if db.delete_card(id): 
            logger.info("Команда /delete отработала успешно")
            bot.send_message(message.chat.id, "Карточка удалена")
        else:
            logger.error("В команде /delete произошла ошибка")
            bot.send_message(message.chat.id, "Произошла ошибка при удалении(")
    else:
        logger.error("Произошла ошибка при в функции value_unique")
        bot.send_message(message.chat.id, "Произошла ошибка при удалении(")
            
cancel_flag = False

# Команда /showall для отображения всех карточек
@bot.message_handler(commands=['showall'])
def show_all(message):
    '''
    Получает все карточки из базы данных и выводит их.
    '''
    global cancel_flag
    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return 

    logger.info('Вызвана команда /showall')
    cards = db.select_all_cards()
    if not cards: 
        bot.send_message(message.chat.id, "Карточек нет")
        logger.info("Команда /showall отработала успешно")
        return
    if cards is False:
        logger.error("В команде /showall произошла ошбика")
        bot.send_message(message.chat.id, "Произошла ошибка")
        return
    logger.info("Команда /showall отработала успешно")
    for card in cards: 
        show_card(message, card, show_date=True)     
        if cancel_flag: 
            cancel_flag = False
            break

@bot.message_handler(commands=['cancel'])
def send_welcome(message):
    global cancel_flag
    cancel_flag = True

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def udentify_user(message):
    '''
    Подключается к базе данных по id пользователя и выводит основную информацию.
    '''

    if not db.connect_database():
        logger.error("Ошибка в подключении к базе данных")
        return 
    logger.info("Вызвана команда /start")

    # Здесь берем id пользователя
    bb.user_id = message.chat.id

    is_unique = db.value_unique("users", "user_id", bb.user_id)
    if is_unique is True: 
        logger.info("Новый пользователь добавлен в базу данных")
        if db.sql_insert("users") is False:
            bot.send_message(message.chat.id, "Произошла ошибка при знакомстве с пользователем(")
            logger.error("Произошла ошибка в функции sql_insert")
    elif is_unique is False:
        logger.info("Пользователь существует")
    else: 
        bot.send_message(message.chat.id, "Произошла ошибка при знакомстве с пользователем(")
        logger.error("Произошла ошибка в функции value_unique")
        return
    
    cards = get_cards_from_db()
    bot.send_message(message.chat.id, f"Доброго времени суток!\nНужно изучить {len(cards)} карточек")
    
# Обработчик команды /find
@bot.message_handler(commands=['find'])
def choose_parameter(message):
    '''
    1 функция команды /find. 
    Выбора параметра для поиска
    '''
    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return 
    
    logger.info("Вызвана команда /find")
    # Отправляем сообщение с ReplyKeyboardMarkup
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('id')
    button2 = types.KeyboardButton('Подсказка')
    button3 = types.KeyboardButton('Текст')
    keyboard.add(button1, button2, button3)

    bot.send_message(message.chat.id, "Выберите параметр, по которому будем искать карточку", reply_markup=keyboard)
    bot.register_next_step_handler(message, lambda msg: check_find_param(msg, keyboard))

def check_find_param(message, keyboard):
    '''
    2 функция команды /find.
    Проверка выбранного параметра поиска
    '''

    if check_cancel(message):
        return
    param = message.text
    column = ""
    if param == "id":
        column = "card_id"
    elif param == "Подсказка":
        column = "hint"
    elif param == "Текст":
        column = "text"
    else:
        bot.send_message(message.chat.id, "Есть только три варианта. Попробуйте еще", reply_markup=keyboard)
        bot.register_next_step_handler(message, lambda msg: check_find_param(msg, keyboard))
        return

    hide_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Введите значение для поиска", reply_markup=hide_keyboard)
    bot.register_next_step_handler(message, lambda msg: find_card(msg, column))

def find_card(message, column):    
    '''
    3 функция команды /find.
    Находит карточку по введеному значению.
    '''
    if check_cancel(message):
        return
        
    card = db.select_by_value(column, message.text)
    if not card:
        bot.send_message(message.chat.id, "Такой карточки нет")
    else:
        show_card(message, card, show_date=True)
    logger.info("Команда /find отработала успешно")


# Обработчик команды /learn
@bot.message_handler(commands=['learn'])
def get_cards_for_learn(message):
    '''
    1 функция команды /learn.
    Получает карточки, которые созрели для обучения 
    '''
    global cards

    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return 
    
    logger.info("Вызвана команда /learn")

    cards = get_cards_from_db()
    
    if not cards: 
        bot.send_message(message.chat.id, text = "Нет карточек для обучения")
        logger.info("Команда /learn успешно отработала")
        return

    cards.reduce_number_of_cards(10)

    bot.send_message(message.chat.id, text = "Погнали")

    # Отправляем сообщение с ReplyKeyboardMarkup
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Не помню')
    button2 = types.KeyboardButton('Помню')
    keyboard.add(button1, button2)

    bot.send_message(message.chat.id, text = "Вам будет показана карточка. Ваша задача вспомнить текст карточки по подсказке и ответить получилось ли у вас это или нет.", reply_markup=keyboard)   
    show_next_card(message, keyboard)

def show_next_card(message, keyboard):
    '''
    2 функция команды /learn. 
    Отображает следующую карточку для обучения
    '''
    global hint_text, remember_text, current_text, cards
    card = next(cards)

    if card == "Learned everything":
        # Заносим выученные карточки в базу данных
        for card in cards.cards_array:
            nextstudy_days = get_nextstudy_days(card.memlevel)
            nextstudy = get_date_in_x_days(nextstudy_days)
            db.change_card(card.card_id, "memlevel", f"{card.memlevel + 1}") # увеличиваем уровень запоминания карточки
            db.change_card(card.card_id, "nextstudy", f"{nextstudy}") 

        cards = get_cards_from_db()
        hide_keyboard = types.ReplyKeyboardRemove()
        cards_number = len(cards)
        if cards_number == 0:
            bot.send_message(message.chat.id, f"Вы изучили все карточки", reply_markup=hide_keyboard)
        else: 
            bot.send_message(message.chat.id, f"Осталось изучить {cards_number} карточек\nЧтобы продолжить введите команду /learn", reply_markup=hide_keyboard)
        
        logger.info("Команда /learn успешно отработала")
        return
    
    hint_text = card.hint
    current_text = remember_text = card.text

     # Отправляем сообщение с InlineKeyboardMarkup
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Перевернуть карточку", callback_data="change_text")
    markup.add(button)
    message_for_ban = bot.send_message(message.chat.id, text = hint_text, reply_markup=markup)

    bot.register_next_step_handler(message, lambda msg: check_answer(msg, keyboard, message_for_ban))

def check_answer(message, keyboard, message_for_ban):
    '''
    3 функция команды /learn.
    Проверяет ответ пользователя.
    '''
    global cards, current_text
    if check_cancel(message):
        return
    
    answer = message.text
    card = cards.get_last_card()
    if answer == "Помню" or answer == card.text:
        bot.send_message(message.chat.id, text = "Отлично!", reply_markup=keyboard)
        cards.reduce_card_repetition() # увеличиеваем repetitions_number
    else:
        bot.send_message(message.chat.id, "Запомните карточку получше. Мы к ней еще вернемся. Следующая карточка:", reply_markup=keyboard)
        cards.reduce_card_memlevel() # уменьшаем значение memlevel для лучшего запоминания
    
    card = cards.get_last_card()
    text = card.get_info()
    bot.edit_message_text(chat_id=message_for_ban.chat.id, message_id=message_for_ban.message_id, text=text)
    # Переходим к следующей карточке
    show_next_card(message, keyboard)

# Обработчик команды /learnall. Команда проходится по всем карточкам, не изменяя их memlevel и nextstudy
@bot.message_handler(commands=['learnall'])
def get_cards_for_learnall(message):
    '''
    1 функция команды /learnall
    Получает все подряд карточки
    '''
    global cards 

    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return 
    
    logger.info("Вызвана команда /learnall")
    cards = Cards()

    # Выбираем все карточки
    cards_to_study = db.select_where_condition(f"0 <= memlevel")

    if cards_to_study:
        for card in cards_to_study:
            cards.add_card(card, repetitions_number=1) # карточки для повторения нужно повторить только один раз 

    if not cards.exists(): 
        bot.send_message(message.chat.id, text = "Нет карточек для обучения")
        logger.info("Команда /learnall успешно отработала")
        return

    bot.send_message(message.chat.id, text = "Погнали")

    # Отправляем сообщение с ReplyKeyboardMarkup
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Не помню')
    button2 = types.KeyboardButton('Помню')
    keyboard.add(button1, button2)

    bot.send_message(message.chat.id, text = "Вам будет показана карточка. Ваша задача вспомнить текст карточки по подсказке и ответить получилось ли у вас это или нет.", reply_markup=keyboard)   

    repeat_next_card(message, keyboard)


def repeat_next_card(message, keyboard):
    '''
    2 функция команды /learnall.
    Получает следующую карточку для повторения
    '''
    global hint_text, remember_text, current_text, cards
    card = next(cards)

    if card == "Learned everything":
        hide_keyboard = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, f"Вы прошлись по всем карточкам!", reply_markup=hide_keyboard)
        logger.info("Команда /learnall успешно отработала")
        return
    
    hint_text = card.hint
    current_text = remember_text = card.text

    # Отправляем сообщение с InlineKeyboardMarkup
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Перевернуть карточку", callback_data="change_text")
    markup.add(button)
    message_for_ban = bot.send_message(message.chat.id, text = hint_text, reply_markup=markup)

    bot.register_next_step_handler(message, lambda msg: check_answ(msg, keyboard, message_for_ban))

def check_answ(message, keyboard, message_for_ban):
    '''
    3 функция команды /learnall 
    Проверяет ответ пользователя
    '''
    global cards, current_text
    if check_cancel(message):
        return
    
    answer = message.text
    card = cards.get_last_card()
    if answer == "Помню" or answer == card.text:
        bot.send_message(message.chat.id, text = "Отлично! Следующая карточка:", reply_markup=keyboard)
        cards.reduce_card_repetition()
    else:
        bot.send_message(message.chat.id, "Запомните карточку получше. Мы к ней еще вернемся. Следующая карточка:", reply_markup=keyboard)
    
    card = cards.get_last_card()
    text = card.get_info()
    bot.edit_message_text(chat_id=message_for_ban.chat.id, message_id=message_for_ban.message_id, text=text)
    # Переходим к следующей карточке
    repeat_next_card(message, keyboard)

# Обработчик нажатия на кнопку "Перевернуть карточку"
@bot.callback_query_handler(func=lambda call: call.data == "change_text")
def callback_change_text(call):
    '''
    Функция для имитация переворачивания флешкарточки
    '''
    global current_text, hint_text, remember_text, cards
    logger.info("Вызван обработчик кнопки для переворота карточки")

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
    logger.info("Обрабочик кнопки для перевортора карточки успешно отработал")


# Обработчик команды /newcard
@bot.message_handler(commands=['newcard'])
def add_new_card(message):    
    '''
    1 функция команды /newcard
    Запрашивает информацию для новой карточки 
    '''
    if not bb.connection:
        bot.send_message(message.chat.id, "Сначала введите команду /start")
        return 
    
    logger.info("Вызвана команда /newcard")
    bot.send_message(message.chat.id, "Введите информацию, которую хотите запомнить")
    bot.register_next_step_handler(message, get_remember_text)

def get_remember_text(message):
    '''
    2 функция команды /newcard
    Проверяет введенную информацию и запрашивает подсказку для карточки
    '''
     
    if check_cancel(message):
        return
    
    text = message.text
    is_unique = db.value_unique("cards", "text", text)
    if is_unique == -1:         
        bot.send_message(message.chat.id, "Произошла ошибка(")
        return
    
    if not is_unique:
        bot.send_message(message.chat.id, "Карточка с таким текстом уже есть, попробуйте другой")
        bot.register_next_step_handler(message, get_remember_text)
        return
    bot.send_message(message.chat.id, "Введите подсказку, по которой будете вспоминать")
    bot.register_next_step_handler(message, lambda msg: get_hint(msg, text))

def get_hint(message, text):
    '''
    3 функция команды /newcard
    Проверет введенную подсказку 
    '''
    if check_cancel(message):
        return
    
    if not db.value_unique("cards", "hint", message.text):
        bot.send_message(message.chat.id, "Карточка с такой подсказкой уже есть, попробуйте другую")
        bot.register_next_step_handler(message, lambda msg: get_hint(msg, text))
        return

    if db.sql_insert(table="cards", text=text, hint=message.text, user_id=message.chat.id) is False: 
        bot.send_message(message.chat.id, "Произошла ошибка. Карточка не добавлена(")
        logger.error("Произошла ошибка в фукнции sql_insert")
        return 
    
    bot.send_message(message.chat.id, "Карточка для запоминания успешно добавлена!")
    logger.info("Команда /newcard успешно отработала")


from requests.exceptions import ReadTimeout

while True:
    try:
        # Устанавливаем большое значение тайм-аута
        bot.polling(none_stop=True, interval=0, timeout=600)
    except ReadTimeout:
        print("ReadTimeout occurred. Retrying...")
    except Exception as e:
        print(f"An error occurred: {e}")
        break