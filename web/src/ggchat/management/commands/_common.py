import logging
import logging.handlers


def setup_logger(log_level):
    logging.basicConfig(
        format='%(asctime)-15s %(processName)-12s %(levelname)-8s %(message)s',
        level=log_level,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                filename='ws_client.log',
                maxBytes=10 * (2 ** 20),  # 10 MB
                backupCount=10,
            ),
        ],
    )
    return logging.getLogger()
