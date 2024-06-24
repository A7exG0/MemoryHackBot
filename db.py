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

def user_exist(connection, user_id):

    query = f"SELECT * FROM Memory_bot.users WHERE user_id = {user_id}"

    with connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            result = cursor.fetchone()
            return result is not None
            
        except Error as e:
            print(f"Ошибка запроса SQL: {e}")
            return True
        
def data_unique(connection, column, value):

    query = f"SELECT * FROM Memory_bot.cards WHERE {column} = '{value}'"
    print(query)
    with connection.cursor() as cursor:
        try: 
            print("!")
            cursor.execute(query)
            result = cursor.fetchone()
            print(result)
            return result is None
            
        except Error as e:
            print(f"Ошибка запроса SQL: {e}")
            return False

def add_card(connection, text, hint, user_id): 

    query = f"INSERT Memory_bot.cards(text, hint, user_id) VALUES('{text}', '{hint}', {user_id})"

    with connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            connection.commit()
            return True
        except Error as e:
            print(f"Ошибка запроса SQL: {e}")
            return False

def add_user(connection, user_id): # можно совместить в функцию insert 

    query = f"INSERT Memory_bot.users(user_id) VALUES({user_id})"

    with connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            connection.commit()

        except Error as e:
            print(f"Ошибка запроса SQL: {e}")

