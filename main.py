import telebot

with open("./token.txt", "r", ) as file:
    token = file.read()

bot = telebot.TeleBot(token)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")

bot.polling(none_stop=True, interval=0)