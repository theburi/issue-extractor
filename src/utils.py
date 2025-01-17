import logging
import yaml
from pathlib import Path
from typing import List, Dict

def load_configuration() -> Dict:
    config_path = Path("./config/config.yaml")
    config = []
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        raise

    try:
        with open(Path(config["paths"]["taxonomy"]), 'r') as f:
            config["taxonomy"] = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load taxonomy: {e}")
        raise
    logging.info("Configuration loaded successfully")
    return config