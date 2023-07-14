from src.main import main, setup_logger, Labirint
import logging
from dotenv import load_dotenv
import os


if __name__ == "__main__":

    load_dotenv()
    setup_logger(os.getenv("LOG_DIR"))

    try:
        main()
    except KeyboardInterrupt:
        logging.info("CTRL+C recieved, stopping an app")
    except Exception as e:
        logging.error("Unexpected error happened")
        logging.critical(e, exc_info=True)
