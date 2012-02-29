import logging
from django.conf import settings

logger = logging.getLogger("kindle.io")
if not logger.handlers:
    handler = logging.FileHandler(settings.LOG_KINDLEIO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s\n%(message)s\n')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
