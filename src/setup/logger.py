"""setting up a custom logger"""

import logging
import sys

def get_logger(logger_name="fraud_pipeline"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
        
    # format of the log message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
        
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
        
    return logger