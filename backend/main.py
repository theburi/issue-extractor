import logging
from typing import List, Dict
from flask import Flask, request, jsonify  # Added for Flask API


from src.api.dashboard import dashboard_bp
from src.api.projects import projects_bp
from src.api.jira import jira_bp
from src.api.config import config_bp
from src.api.issues import issues_bp
from src.api.process import process_bp
from src.utils import load_configuration



# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)  # Initialize Flask app


# Register the Blueprint
app.register_blueprint(dashboard_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(jira_bp)
app.register_blueprint(config_bp)
app.register_blueprint(issues_bp)
app.register_blueprint(process_bp)

if __name__ == "__main__":
    app.run(debug=True, port=4000)  # Change port to 5000
