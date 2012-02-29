import logging
from django.conf import settings

logger = logging.getLogger("kindle.io")
if not logger.handlers:
    handler = logging.FileHandler(settings.LOG_ERROR_KINDLEIO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s\n%(message)s\n')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

logger_info = logging.getLogger("kindle.io.info")
if not logger_info.handlers:
    handler = logging.FileHandler(settings.LOG_INFO_KINDLEIO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s\n%(message)s\n')
    handler.setFormatter(formatter)
    logger_info.addHandler(handler)
    logger_info.setLevel(logging.INFO)

