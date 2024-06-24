import mysql.connector
from mysql.connector import Error
from datetime import date

import configparser
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

        # Создание курсора для выполнения SQL-запросов
        cursor = connection.cursor()

except Error as e:
    print(f"Ошибка подключения к MySQL: {e}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("Подключение к MySQL закрыто")
