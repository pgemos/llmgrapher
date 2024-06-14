import logging
import sys
from llmgrapher import config

LOGGER_FILE = f"{config.PROJ_ROOT}/logs/{config.PROJ_NAME}.log"

def setup_logger(logger_file):
    logger = logging.getLogger("__name__")
    logger.setLevel(logging.DEBUG)  # only log the current logger in DEBUG mode
    logging.basicConfig(
        level=logging.CRITICAL,  # show only CRITICAL messages from other loggers
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8",
        handlers=[  # output log messages to both file and stdout
            logging.FileHandler(logger_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logger

logger = setup_logger(LOGGER_FILE)

logger.info(f"PROJ_ROOT path is: {config.PROJ_ROOT}")
