import mysql.connector 
from mysql.connector import Error
import configparser

def connect_database():
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Параметры подключения
    host = config['database']['host']
    database = config['database']['database']
    user = config['database']['user']
    password = config['database']['password']

    # Подключение к базе данных
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        if connection.is_connected():
            print("Успешное подключение к базе данных")
            return connection  # Возвращаем соединение

    except Error as e:
        print(f"Ошибка подключения к MySQL: {e}")
        return None  # Возвращаем None в случае ошибки

def value_unique(connection, table, column, value):
    '''
    Проверяет уникальность value в column.
    Возвращает True, если такого значения нет.
    Возвращает -1 в случае ошибки.
    '''
    if type(value) == str:
        value = "'" + value + "'"
    else: 
        value = str(value)

    query = f"SELECT * FROM Memory_bot.{table} WHERE {column} = {value}"

    with connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            result = cursor.fetchone()
            return result is None
            
        except Error as e:
            print(f"Ошибка запроса SQL: {e}")
            return -1


def sql_insert(connection, table, **kwargs):
    '''
    Функция принимает connection базы данных и таблицу в которую будут вставляться данные. 
    Далее параметры будут по названию будут записываться в соответствующий столбец. 
    Пример: 
        sql_insert(connection, cards, id=12342)
    В данном случае в столбец id запишеться соответствующее значение.
    '''
    columns = values = ""
    for key, value in kwargs.items():
        columns += key + ","
        if type(value) == str:
            values += "'" + value + "',"
        else: # не знаю, сработает ли это для datetime
            values += str(value) + ","
            
    # Удаляем последнюю запятую 
    values = values[:len(values)-1]
    columns = columns[:len(columns)-1]

    query = f"INSERT Memory_bot.{table}({columns}) VALUES({values})"

    with connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            connection.commit()
            return True

        except Error as e:
            print(f"Ошибка запроса SQL: {e}")
            return False

def select_cards(connection): 
    
    query = "SELECT card_id, text, hint FROM cards"

    with connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows

        except Error as e:
            print(f"Ошибка запроса SQL: {e}")
            return False
    # Получение всех строк результата запроса
    