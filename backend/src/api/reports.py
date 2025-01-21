
import logging
from typing import List, Dict
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from bson import ObjectId 
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
reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports', methods=['GET'])
def get_reports():
    project_id = request.args.get('projectid')
    if not project_id:
        return jsonify({'error': 'Project ID is required'}), 400

    try:
        # Query the reports collection for the specified project_id
        report = db[config["mongodb"]["reports_collection"]].find_one({"project_id": project_id})
        if not report:
            return jsonify({'error': 'Report not found for the given Project ID'}), 404

        # Return the report data
        return jsonify({
            'project_id': report['project_id'],
            'report_html': report['report_html'],
            'report_data': report['report_data']
        }), 200

    except Exception as e:
        logging.error(f"Error retrieving report for project_id {project_id}: {str(e)}")
        return jsonify({'error': 'An error occurred while retrieving the report'}), 500