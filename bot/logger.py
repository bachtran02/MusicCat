import os
import logging.config

log_path = os.path.join(os.getcwd(), 'log')

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
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
            'filename': f'{log_path}\\track.log',
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
