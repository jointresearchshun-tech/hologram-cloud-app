import logging




def setup_logging(level=logging.INFO):
logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
return logging.getLogger("cloud-hologram-app")




logger = setup_logging()
