import logging
import sys


def setup_logging(level: int) -> None:
    for package in ["pystac", "tests"]:
        logger = logging.getLogger(package)
        logger.setLevel(level)

        formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)


setup_logging(logging.INFO)
