from flask import Blueprint, request, jsonify
import logging
from src.utils import load_configuration
from src.db.mongodb_client import connect_to_mongo
from src.llm_utils import invoke_llm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration
config = load_configuration()

# Create a Blueprint for the issues API
issues_bp = Blueprint('issues', __name__)

# Connect to MongoDB
db = connect_to_mongo(
    config["mongodb"]["uri"], config["mongodb"]["database"])
collection = db[config["mongodb"]["raw_collection"]]  # Replace with your collection name

@issues_bp.route('/api/issues/count', methods=['GET'])
def get_issue_count():
    """
    Endpoint to count issues for a specific project.
    """
    try:
        # Get the project ID from query parameters
        project_id = request.args.get('project')
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400

        # Query MongoDB for issues count by project
        count = collection.count_documents({'project_id': project_id})

        # Return the count
        return jsonify({'count': count}), 200

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'error': 'An error occurred while fetching issue count', 'details': str(e)}), 500
    
@issues_bp.route('/api/issues/summary', methods=['POST'])
def get_issue_summary():

    data = request.get_json()
    
    if 'variables' not in data:
        return jsonify({'error': 'variables is required in the request body'}), 400
    if 'prompt' not in data:
        return jsonify({'error': 'prompt is required in the request body'}), 400

    issueText = data['variables']
    promt = data['prompt']

    result = invoke_llm(config, promt, issueText)

    return jsonify({'summary': result}), 200
