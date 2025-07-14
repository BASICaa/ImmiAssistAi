import logging
import os

class AppLogger:
    def __init__(self, log_file='app_debug.log', log_level=logging.DEBUG):
        # Correctly join paths to place logs in the project root
        self.log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', log_file)
        self.log_level = log_level
        self.logger = self.setup_logger()

    def setup_logger(self):
        # Create a logger
        logger = logging.getLogger(__name__)
        logger.setLevel(self.log_level)

        # Create a file handler that overwrites the file
        file_handler = logging.FileHandler(self.log_file, mode='w')
        file_handler.setLevel(self.log_level)

        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a formatter and set it for the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def get_logger(self):
        return self.logger

# Example usage:
# from logging_config import AppLogger
# logger = AppLogger().get_logger()
# logger.debug("This is a debug message.")
# logger.info("This is an info message.")
# logger.warning("This is a warning message.")
# logger.error("This is an error message.")
# logger.critical("This is a critical message.")