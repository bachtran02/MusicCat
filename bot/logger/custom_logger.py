import os
import logging.config

log_paths = {}
loggers = ['track', 'command']

for logger in loggers:
    path = os.path.join(os.getcwd(), 'logs', f'{logger}.log')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    log_paths[logger] = path

logging.config.dictConfig({
    'version': 1,
    'level': 'DEBUG',
    'disable_existing_loggers': False,
    'loggers': {
        'track_logger': {
            'handlers': ['track_logging_handler', 'console_handler'],
            'level': 'INFO',
            'propagate': False
        },
        'command_logger': {
            'handlers': ['command_logging_handler', 'console_handler'],
            'level': 'INFO',
            'propagate': False
        }
    },

    'handlers': {
        'track_logging_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': log_paths['track'],
            'mode': 'a',
            'encoding': 'utf-8'
        },
        'command_logging_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': log_paths['command'],
            'mode': 'a',
            'encoding': 'utf-8'
        },
        'console_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'stream': 'ext://sys.stdout', 
        },
    },

    'formatters': {
        'default': {
            'format': '%(asctime)s: %(message)s'
        },
        'console': {
            '()': 'colorlog.ColoredFormatter',
            'format': 
                "%(log_color)s%(bold)s%(levelname)-1.1s%(thin)s "
                "%(asctime)23.23s "
                "%(bold)s%(name)s: "
                "%(thin)s%(message)s%(reset)s"
        },
    },
})

track_logger = logging.getLogger('track_logger')
command_logger = logging.getLogger('command_logger')