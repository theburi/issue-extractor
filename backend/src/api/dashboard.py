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
    issue_stats = jsonify(list(stats))
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
    issue_stats = jsonify(list(stats))
    return issue_stats, 200

@dashboard_bp.route('/api/jira-issues', methods=['POST'])
def get_jira_issues():
    query = request.json.get('query')
    issues_df = extract_issues(query)
    issues = issues_df.to_dict(orient='records')
    return jsonify(issues), 200

@dashboard_bp.route('/api/start', methods=['POST'])
def start_analysis():
    issues = request.json.get('issues')
    # Placeholder for analysis logic
    report = {"status": "Analysis started", "issues_count": len(issues)}
    
    def run_analysis():
        # Add your analysis logic here
        logging.info("Running analysis on issues")
        # Simulate analysis with sleep
        import time
        time.sleep(5)
        logging.info("Analysis completed")
    
    analysis_thread = threading.Thread(target=run_analysis)
    analysis_thread.start()
    
    return jsonify(report), 200


