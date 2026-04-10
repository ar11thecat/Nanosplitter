import logging
import sys


color = "\x1b[37m"
reset = "\x1b[0m"
    
logging.basicConfig(
    level=logging.INFO,
    format=color + "%(asctime)s [%(levelname)s] %(name)s: %(message)s" + reset,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
