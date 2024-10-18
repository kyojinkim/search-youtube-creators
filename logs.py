import logging
import sys

def setup_logger(name, level=logging.DEBUG):
    """configure logger"""
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create stream handler for console
    stream_handler = logging.StreamHandler(sys.stdout)
    
    # formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)

    #
    logger.addHandler(stream_handler)

    return logger

# global logger
def setup_global_logger(level=logging.DEBUG):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )