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


def exec_select_query(connection, query):
    with connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            result = cursor.fetchall()
            return result

        except Error as e:
            print(f"Ошибка запроса SQL: {e}")
            return -1
        
def exec_commit_query(connection, query):
    with connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            connection.commit()
            return True

        except Error as e:
            print(f"Ошибка запроса SQL: {e}")
            return -1

def correct_value(value):
    '''
    Функция нужна для того, чтобы подготовить значения для sql запроса
    '''
    if type(value) == str:
        value = "'" + value + "'"
    else: 
        value = str(value)
    return value

def value_unique(connection, table, column, value):
    '''
    Проверяет уникальность value в column.
    Возвращает True, если такого значения нет.
    Возвращает -1 в случае ошибки.
    '''
    sql_value = correct_value(value)

    query = f"SELECT * FROM Memory_bot.{table} WHERE {column} = {sql_value}"

    result = exec_select_query(connection, query)
    if result == -1:
        return result 
    else:
        return not result

 
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
        sql_value = correct_value(value)
        values+= sql_value + ","
            
    # Удаляем последнюю запятую 
    values = values[:len(values)-1]
    columns = columns[:len(columns)-1]

    query = f"INSERT Memory_bot.{table}({columns}) VALUES({values})"

    return exec_commit_query(connection, query)

        
def select_all_cards(connection): 
    query = "SELECT card_id, text, hint FROM cards"
    return exec_select_query(connection, query)

        
def select_by_value(connection, column, value): 
    if column != "card_id": # подготавливаем значение, только если поиск не в card_id колонке, так как там значения int
        value = correct_value(value)
    
    query = f"SELECT card_id, text, hint FROM cards WHERE {column} = {value}"
    result = exec_select_query(connection, query)
    if result:
        return result[0]
    else:
        return None
    
def delete_card(connection, id):
    query = f"DELETE FROM cards WHERE card_id = {id}"
    return exec_commit_query(connection, query) 



    