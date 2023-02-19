import os
import logging.config

log_path = {}
log_name = ['track', 'bot']

for log in log_name:
    path = os.path.join(os.getcwd(), 'logs', f'{log}.log')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    log_path[log] = path

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
            'filename': log_path['bot'],
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

logging.config.dictConfig({
    'version': 1,
    'level': 'DEBUG',
    'disable_existing_loggers': False,
    'loggers': {
        'track_logger': {
            'handlers': ['track_logging_handler'],
            'level': 'INFO',
            'propagate': False
        }
    },

    'handlers': {
        'track_logging_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'track_logging_format',
            'filename': log_path['track'],
            'mode': 'a',
            'encoding': 'utf-8'
        },
    },

    'formatters': {
        'track_logging_format': {
            'format': '%(asctime)s: %(message)s'
        },
    },
})

track_logger = logging.getLogger('track_logger')
