import uuid
from flask import Blueprint, request, jsonify
import asyncio
import logging
from src.jira_extractor import main_execution_flow
import threading
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Create a Blueprint
jira_bp = Blueprint('jira', __name__)

# In-memory task store (use a database for production)
tasks = {}

def long_running_task(task_id, project_id):
    try:
        # Update task status to "in_progress"
        tasks[task_id]['status'] = 'in_progress'

        # Simulate a long-running operation
        count, project_id = main_execution_flow(project_id)

        # Mark task as completed and store result
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result'] = f"Extraction of {count} issues completed for project {project_id}"
    except Exception as e:
        # Handle task errors
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['result'] = str(e)

@jira_bp.route('/api/jira/extract', methods=['GET'])
async def extract_jira_data():
    project_id = request.args.get('project')
    if not project_id:
        return jsonify({'error': 'Project ID is required'}), 400

    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    # Add task to the task store
    tasks[task_id] = {'status': 'pending', 'result': None}

    # Start the long-running task in a separate thread
    thread = threading.Thread(target=long_running_task, args=(task_id, project_id))
    thread.start()

    # Return the task ID to the client
    return jsonify({'task_id': task_id}), 202

@jira_bp.route('/api/jira/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
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