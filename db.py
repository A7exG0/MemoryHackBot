import mysql.connector 
from mysql.connector import Error
import configparser
from bot_logging import logger
import bb

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
        bb.connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        if bb.connection.is_connected():
            logger.info("Подключение к базе данных прошло успешно")
            return 1  # Возвращаем соединение

    except Error as e:
        logger.error(f"Ошибка подключения к MySQL: {e}")
        return None  # Возвращаем None в случае ошибки


def exec_select_query(query):
    with bb.connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            result = cursor.fetchall()
            return result

        except Error as e:
            logger.error(f"Ошибка запроса SQL: {e}")
            return -1
        
def exec_commit_query(query):
    with bb.connection.cursor() as cursor:
        try: 
            cursor.execute(query)
            bb.connection.commit()
            return True

        except Error as e:
            logger.error(f"Ошибка запроса SQL: {e}")
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

def value_unique(table, column, value, group = None):
    '''
    Проверяет уникальность value в column.
    Возвращает True, если такого значения нет.
    Возвращает -1 в случае ошибки.
    '''
    sql_value = correct_value(value)

    query = f"SELECT * FROM Memory_bot.{table} WHERE {column} = {sql_value}"
    
    if group is not None:
        query += f" and `group` = '{group}'"
    result = exec_select_query(query)
    if result == -1:
        return result 
    else:
        return not result

 
def sql_insert(table, group=None, **kwargs): 
    '''
    Параметры будут по названию будут записываться в соответствующий столбец. 
    Пример: 
        sql_insert(cards, id=12342)
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
    
    if group is not None:
        columns += ", `group`"
        values += f", '{bb.group}'"

    query = f"INSERT Memory_bot.{table}({columns}) VALUES({values})"
    print(query)
    return exec_commit_query(query)

        
def select_all_cards(): 
    query = f"SELECT card_id, text, hint, memlevel, nextstudy FROM memory_bot.cards WHERE `group` = '{bb.group}' and user_id = {bb.user_id}"
    return exec_select_query(query)

        
def select_by_value(column, value): 
    if column != "card_id": # подготавливаем значение, только если поиск не в card_id колонке, так как там значения int
        value = correct_value(value)
    
    query = f"SELECT card_id, text, hint, memlevel, nextstudy FROM memory_bot.cards WHERE {column} = {value} and `group` = '{bb.group}' and user_id = {bb.user_id}"
    result = exec_select_query(query)
    if result:
        return result[0]
    else:
        return None
    
def select_where_condition(condition): 
    
    query = f"SELECT card_id, text, hint, memlevel, nextstudy FROM memory_bot.cards WHERE {condition} and `group` = '{bb.group}' and user_id = {bb.user_id}"
    result = exec_select_query(query)
    if result:
        return result
    else:
        return None
    
def delete_card(id):
    query = f"DELETE FROM memory_bot.cards WHERE card_id = {id} and `group` = '{bb.group}' and user_id = {bb.user_id}"
    return exec_commit_query(query) 

def change_card(id, column, value):
    query = f"UPDATE memory_bot.cards SET {column} = '{value}' WHERE card_id = {id} and `group` = '{bb.group}' and user_id = {bb.user_id}"
    return exec_commit_query(query)
    
def select_all_groups():
    query = f"SELECT DISTINCT `group` FROM memory_bot.cards WHERE user_id = {bb.user_id}"
    return exec_select_query(query)