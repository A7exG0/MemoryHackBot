import configparser
import telebot

# Получаем токен бота из файла config.ini
config = configparser.ConfigParser()
config.read('config.ini')
token = config['token']['value']

bot = telebot.TeleBot(token)
connection = None
group = "DEFAULT"
user_id = None
