import uuid
from flask import Blueprint, request, jsonify
import logging
import threading
import time
from src.analysis import main_execution_flow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create a Blueprint
process_bp = Blueprint('process', __name__)

# In-memory task store (use a database for production)
tasks = {}

def long_running_process(task_id, projectId, stage):
    """
    Simulate a long-running process for a given stage.
    """
    try:
        # Update task status to "in_progress"
        tasks[task_id]['status'] = 'in_progress'

        main_execution_flow(projectId, stage)

        # Example result based on stage
        result = f"Processing for stage {stage} completed successfully"

        # Mark task as completed and store result
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result'] = result

    except Exception as e:
        # Handle task errors
        logging.error(f"Error in task {task_id}: {str(e)}", exc_info=True)
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['result'] = str(e)

@process_bp.route('/api/process', methods=['GET'])
def start_process():
    """
    Start a long-running process for a specific stage.
    """
    stage = int( request.args.get('stage'))
    projectId = request.args.get('project_id')
    if not stage:
        return jsonify({'error': 'Stage is required'}), 400
    if not projectId:
        return jsonify({'error': 'Project is required'}), 400

    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    # Add task to the task store
    tasks[task_id] = {'status': 'pending', 'result': None}

    # Start the long-running process in a separate thread
    thread = threading.Thread(target=long_running_process, args=(task_id, projectId, stage))
    thread.start()

    # Return the task ID to the client
    return jsonify({'task_id': task_id}), 202

@process_bp.route('/api/process/status/<task_id>', methods=['GET'])
def get_process_status(task_id):
    """
    Get the status of a long-running process by task ID.
    """
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