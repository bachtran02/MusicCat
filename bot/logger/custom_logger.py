import os
import logging.config

log_paths = {}
loggers = ['track']

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
            'handlers': ['track_logging_handler'],
            'level': 'INFO',
            'propagate': False
        }
    },

    'handlers': {
        'track_logging_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'track_logging_format',
            'filename': log_paths['track'],
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