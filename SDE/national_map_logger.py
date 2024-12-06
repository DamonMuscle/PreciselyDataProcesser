import logging
from logging.handlers import RotatingFileHandler
import arcpy

from national_map_utility import NationalMapUtility


class NationalMapLogger:
    logger = None

    @staticmethod
    def init(configuration):
        out_log_folder = configuration.data['Outputs']['log_folder']
        NationalMapUtility.ensure_path_exists(out_log_folder)

        NationalMapLogger.logger = logging.getLogger(__name__)

        log_file = configuration.data['Outputs']['log']
        file_handler = RotatingFileHandler(log_file, mode='a', maxBytes=10_100_000, encoding='utf-8')
        formatter = logging.Formatter(
            '{asctime}\t{levelname}:\t\t{message}',
            style='{',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        if NationalMapLogger.logger.hasHandlers():
            NationalMapLogger.logger.handlers.clear()
        NationalMapLogger.logger.addHandler(file_handler)

        log_level = configuration.data['Logging']['log_level']
        NationalMapLogger.logger.setLevel(log_level)

    @staticmethod
    def start_log_process(process_name):
        NationalMapLogger.logger.info(f'START {process_name}')

    @staticmethod
    def stop_log_process(process_name):
        NationalMapLogger.logger.info(f'STOP {process_name}')

    @staticmethod
    def show_message(message):
        arcpy.AddMessage(message)
        NationalMapLogger.logger.info(message)

    @staticmethod
    def set_arcpy_progressor_label(label):
        arcpy.SetProgressorLabel(label)
        NationalMapLogger.logger.debug(label)

    @staticmethod
    def info(message):
        print(message)
        NationalMapLogger.logger.info(message)

    @staticmethod
    def debug(message):
        print(message)
        NationalMapLogger.logger.debug(message)

    @staticmethod
    def warning(message):
        print(f'WARN: {message}')
        NationalMapLogger.logger.warning(message)

    @staticmethod
    def error(message):
        print(f'ERROR: {message}')
        NationalMapLogger.logger.error(message)

    @staticmethod
    def close_logger():
        for handler in NationalMapLogger.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
