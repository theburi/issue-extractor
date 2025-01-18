from flask import Blueprint, Flask, jsonify, request
from pymongo import MongoClient
import logging
import threading

from src.utils import load_configuration
from src.db.mongodb_client import connect_to_mongo
from src.jira_extractor import extract_issues

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration
config = load_configuration()

# Connect to MongoDB
db = connect_to_mongo(
    config["mongodb"]["uri"], config["mongodb"]["database"])

# Create a Blueprint
projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/api/projects', methods=['GET'])
def get_projects():
    projects = list(db.projects.find({}))
    return jsonify(projects), 200

@projects_bp.route('/api/projects', methods=['POST'])
def create_project():
    project_name = request.json.get('name')
    new_project = {'name': project_name}
    result = db.projects.insert_one(new_project)
    new_project['_id'] = str(result.inserted_id)
    return jsonify(new_project), 201

