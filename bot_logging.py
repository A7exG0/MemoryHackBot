import logging

# Настройка логирования в файл
logging.basicConfig(filename='bot.log', 
                    filemode='w', 
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)