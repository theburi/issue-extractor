from flask import Blueprint, Flask, jsonify, request
import logging
import yaml
from pathlib import Path

from src.utils import load_configuration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration
config = load_configuration()

# Create a Blueprint
config_bp = Blueprint('config', __name__)

@config_bp.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    logging.info ("Inside manage_config")
    config_path = Path("./config/config.yaml")
    if request.method == 'GET':
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return jsonify(config), 200
    elif request.method == 'POST':
        new_config = request.json
        with open(config_path, 'w') as f:
            yaml.safe_dump(new_config, f)
        return jsonify({"status": "success"}), 200