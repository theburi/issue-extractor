from flask import Blueprint, request, jsonify
import logging
import threading
import uuid
from src.utils import load_configuration
from src.db.mongodb_client import connect_to_mongo
from src.llm_utils import invoke_llm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# In-memory task store (use a database for production)
tasks = {}

# Load configuration
config = load_configuration()

# Create a Blueprint for the issues API
issues_bp = Blueprint('issues', __name__)

# Connect to MongoDB
db = connect_to_mongo(
    config["mongodb"]["uri"], config["mongodb"]["database"])
collection = db[config["mongodb"]["raw_collection"]]  # Replace with your collection name

def long_running_process(task_id, config, promt, issueText):
    """
    Simulate a long-running process for a given stage.
    """
    try:
        # Update task status to "in_progress"
        tasks[task_id]['status'] = 'in_progress'

        invoke_llm(config, promt, issueText)

        # Example result based on stage
        result = f"Processing LLM completed successfully"

        # Mark task as completed and store result
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result'] = result

    except Exception as e:
        # Handle task errors
        logging.error(f"Error in task {task_id}: {str(e)}", exc_info=True)
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['result'] = str(e)

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
    try:
        data = request.get_json()
    
        if 'variables' not in data:
            return jsonify({'error': 'variables is required in the request body'}), 400
        if 'prompt' not in data:
            return jsonify({'error': 'prompt is required in the request body'}), 400
        
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        # Add task to the task store
        tasks[task_id] = {'status': 'pending', 'result': None}

        print("get_issue_summary")
        issueText = data['variables']
        promt = data['prompt']
        print("get_issue_summary2")

        # Start the long-running process in a separate thread
        thread = threading.Thread(target=long_running_process, args=(task_id,config, promt, issueText))
        thread.start()

        # Return the task ID to the client
        return jsonify({'task_id': task_id}), 202
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching issue summary', 'details': str(e)}), 500

@issues_bp.route('/api/issues/summary/tasks/<task_id>', methods=['GET'])
def get_process_status(task_id):
    """
    Get the status of a long-running process by task ID.
    """
    try:
        # Check if the task ID exists
        if task_id not in tasks:
            return jsonify({'error': 'Task not found'}), 404

        # Return the status and result of the task
        task = tasks[task_id]
        return jsonify({
            'task_id': task_id,
            'status': task['status'],
            'result': task['result']
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching task status', 'details': str(e)}), 500

