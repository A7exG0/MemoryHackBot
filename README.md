# MemoryHackBot

MemoryHackBot — это бот, предназначенный для запоминания информации с помощью флеш-карточек. Он использует метод интервальных повторений для оптимизации процесса обучения.

## Используемые технологии
- Python
- MySQL

## Инструкции по установке

### Предварительные требования
- Python 3.x
- MySQL

### Пошаговая инструкция

1. **Создайте виртуальное окружение**
   ```bash
   python -m venv venv
   source venv/bin/activate   # На Windows используйте `venv\Scripts\activate`
   ```

2. **Клонируйте репозиторий**
   ```bash
   git clone https://github.com/yourusername/MemoryHackBot.git
   cd MemoryHackBot
   ```

3. **Установите зависимости**
   ```bash
   pip install telebot
   pip install mysql-connector-python
   ```

4. **Настройте базу данных**
   - Запустите сервер MySQL и войдите в MySQL оболочку:
     ```bash
     mysql -u yourusername -p
     ```
   - Создайте новую базу данных:
     ```sql
     CREATE DATABASE memory_bot;
     USE memory_bot;
     ```

5. **Создайте необходимые таблицы**
   ```sql
   CREATE TABLE users (
       user_id VARCHAR(255) NOT NULL PRIMARY KEY,
       numcards INT DEFAULT 0
   );

   CREATE TABLE cards (
       card_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
       text VARCHAR(255) NOT NULL,
       hint VARCHAR(255) NOT NULL,
       memlevel INT DEFAULT 0,
       nextstudy DATETIME DEFAULT '2000-01-01 00:00:00',
       user_id VARCHAR(255),
       `group` VARCHAR(50),
       FOREIGN KEY (user_id) REFERENCES users(user_id)
   );
   ```

6. **Настройте подключение к базе данных**
   - Создайте файл `config.py` в корневом каталоге проекта с вашими данными для подключения к MySQL:
     ```python
     DATABASE = {
         'host': 'localhost',
         'user': 'yourusername',
         'password': 'yourpassword',
         'database': 'memory_bot'
     }
     ```

7. **Запустите бота**
   ```bash
   python main.py
   ```

## Использование
- Бот позволяет пользователям создавать, редактировать и повторять флеш-карточки.
- Карточки классифицируются по группам для удобства управления.
- Бот использует метод интервальных повторений для определения времени следующего повторения карточки.
