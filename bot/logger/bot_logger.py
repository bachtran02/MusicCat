import os

path = os.path.join(os.getcwd(), 'logs', 'bot.log')
os.makedirs(os.path.dirname(path), exist_ok=True)

# for hikari-lighbulb logging
bot_logging_config = {
    'version': 1,
    'level': 'DEBUG',
    'disable_existing_loggers': False,

    'root': {
        'handlers': ['rotating_file_handler', 'console_handler'],
        'level': 'INFO',
    },

    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'rotating_file_handler': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'encoding': 'utf-8',
            'filename': path,
            'formatter': 'file',
            'backupCount': 10,
            'when': 'midnight',
            'utc': False,
        },
    },

    'formatters': {
        'console': {
            '()': 'colorlog.ColoredFormatter',
            'format': 
                "%(log_color)s%(bold)s%(levelname)-1.1s%(thin)s "
                "%(asctime)23.23s "
                "%(bold)s%(name)s: "
                "%(thin)s%(message)s%(reset)s"
        },
        'file': {
            'format':
                "%(asctime)s %(levelname)s %(name)s."
                "%(funcName)s:%(lineno)d: %(message)s"
        }
    },
}
