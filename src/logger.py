import logging

class Logger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.logger = logging.getLogger('job_scraper')
        if not self.logger.hasHandlers():
            self.logger.setLevel(logging.INFO)
            
            # File handler
            file_handler = logging.FileHandler(self.log_file)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
