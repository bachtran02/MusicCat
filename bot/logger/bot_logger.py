import os

path = os.path.join(os.getcwd(), 'logs', 'bot.log')
os.makedirs(os.path.dirname(path), exist_ok=True)

# for hikari-lighbulb logging
bot_logging_config = {
    'version': 1,
    'level': 'DEBUG',
    'disable_existing_loggers': False,

    'root': {
        'handlers': ['file_handler', 'console_handler'],
        'level': 'INFO',
    },

    'handlers': {
        'file_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': path,
            'mode': 'a',
            'encoding': 'utf-8'
        },
        'console_handler': { 
            'level': 'INFO',
            'formatter': 'console',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },

    'formatters': {
        'console': {
            '()': 'coloredlogs.ColoredFormatter', 
            'format': "%(asctime)s %(levelname)s %(name)s.%(funcName)s:%(lineno)d: %(message)s"
        },
        'file': {
            'format': "%(asctime)s %(levelname)s %(name)s.%(funcName)s:%(lineno)d: %(message)s"
        }
    },
}
