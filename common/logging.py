import logging


def get_logger(name, format='%(name)s:%(levelname)s:%(message)s', level=logging.DEBUG):
    logger = logging.getLogger(name)

    if hasattr(logger, 'ptb') and logger.ptb:
        return logger
    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(format)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)

        logger.setLevel(level)
        logger.ptb = True
        return logger
