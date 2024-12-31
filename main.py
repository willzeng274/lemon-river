"""
Lemon river main entry point
"""

import multiprocessing
import logging
import os
import sys
from dotenv import load_dotenv

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QApplication
from voice.listener import stream_record
from voice.transcriber import run_transcriber
from gui.job_window import JobApplicationWindow
from utils import setup_process_logging


def setup_logging(name):
    """
    Setup logging for the given name.
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_dir = os.getenv('LOG_DIR', 'logs')
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    setup_process_logging(level=log_level)
    return logging.getLogger(name)


def run_listener(logger):
    """
    Run the audio listener process.
    """
    logger.info("Starting audio listener")
    try:
        stream_record(logger)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error(f"Error in listener process: {str(e)}", exc_info=True)


def main():
    """
    Main entry point.
    """
    # Load environment variables at the start
    load_dotenv()

    logger = setup_logging("main")
    logger.info("Starting voice assistant")

    logger.debug("Logging directory: %s", os.path.abspath("logs"))

    window_queue = multiprocessing.Queue()
    logger.info("Created communication queues")

    app = QApplication(sys.argv)
    _window = JobApplicationWindow(window_queue)
    logger.info("Created Qt window")

    processes = [
        multiprocessing.Process(target=run_listener, args=(setup_logging("listener"),)),
        multiprocessing.Process(
            target=run_transcriber, args=(setup_logging("transcriber"), window_queue)
        ),
    ]

    for process in processes:
        process.start()
        logger.info("Started process %s", process.name)

    try:
        app.exec()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        for process in processes:
            process.terminate()
            process.join()
        logger.info("All processes terminated")
        sys.exit(0)
    finally:
        for process in processes:
            process.terminate()
            process.join()
        logger.info("All processes terminated")


if __name__ == "__main__":
    main()
