import os
import logging.config

track_log_path = os.path.join(os.getcwd(), 'log', 'track.log')

for path in [track_log_path]:
    os.makedirs(os.path.dirname(path), exist_ok=True)

logging.config.dictConfig({
    'version': 1,
    'level': 'DEBUG',
    'loggers': {
        'track_logger': {
            'handlers': ['track_logger_handler'],
            'level': 'INFO',
        }
    },

    'handlers': {
        'track_logger_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': track_log_path,
            'mode': 'a',
            'encoding': 'utf-8'
        },
    },

    'formatters': {
        'default': {
            'format': '%(asctime)s: %(levelname)s : %(message)s'
        },
    },
})


track_logger = logging.getLogger('track_logger')
