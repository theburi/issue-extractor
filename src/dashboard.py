from flask import Blueprint, Flask, jsonify
from pymongo import MongoClient
import logging

from src.utils import load_configuration
from src.db.mongodb_client import connect_to_mongo

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
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/issues/stats', methods=['GET'])
def get_issues_stats():
    stats = db[config["mongodb"]["raw_collection"]].aggregate([{
            '$group': {
            '_id': '$jira_source', # Group by the 'jira_source' field
            'count': { '$sum': 1 }   # Count the number of documents in each group
            }
        }
        ])
    issue_stats=jsonify(list(stats))
    logging.info(f'getting Issues stats {issue_stats}')
    return issue_stats, 200

@dashboard_bp.route('/api/processed_issues/stats', methods=['GET'])
def get_processed_issues_stats():
    stats = db[config["mongodb"]["processed_collection"]].aggregate([{
            '$group': {
            '_id': '$jira_source', # Group by the 'jira_source' field
            'count': { '$sum': 1 }   # Count the number of documents in each group
            }
        }
        ])
    return jsonify(list(stats)), 200

