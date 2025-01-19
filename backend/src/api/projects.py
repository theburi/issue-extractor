from flask import Blueprint, jsonify, request
from pymongo import MongoClient
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
projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/api/projects', methods=['GET'])
def get_projects():
    logging.info("Get Projects called")
    # Pagination parameters
    range_header = request.args.get('range', '[0,9]')
    start, end = map(int, range_header.strip('[]').split(','))
    limit = end - start + 1

    # Fetch paginated data
    total_projects = db.projects.count_documents({})
    projects_cursor = db.projects.find().skip(start).limit(limit)

    # Convert MongoDB cursor to a list and make _id JSON serializable
    projects = []
    for project in projects_cursor:
        project['id'] = str(project['_id'])  # Convert ObjectId to string
        del project['_id']  # Remove the original _id field
        projects.append(project)

    # Add the Content-Range header
    response = jsonify(projects)
    response.headers['Content-Range'] = f'projects {start}-{min(end, total_projects - 1)}/{total_projects}'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    logging.info(f"Returning projects {start}-{min(end, total_projects - 1)}/{total_projects}")
    return response, 200

@projects_bp.route('/api/projects', methods=['POST'])
def create_project():
    project_name = request.json.get('name')
    jira_source = request.json.get('jira_source')
    prompts = request.json.get('prompts', {})

    new_project = {
        'name': project_name, 
        'jira_source': jira_source,
        'prompts': prompts
        }
    result = db.projects.insert_one(new_project)
    

    # Ensure the response contains an `id` field
    created_project = {
        'id': str(result.inserted_id),  # Use MongoDB's `_id` as `id`
        'name': project_name,
        'jira_source': jira_source,
        'prompts': prompts
    }

    return jsonify(created_project), 201

@projects_bp.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Delete a project by its ID.
    """
    logging.info(f"Delete Project called for ID: {project_id}")

    # Convert the project_id to MongoDB's ObjectId
    try:
        result = db.projects.delete_one({'_id': ObjectId(project_id)})
        
        if result.deleted_count == 1:
            logging.info(f"Project {project_id} successfully deleted.")
            return jsonify({'message': f'Project {project_id} deleted successfully.'}), 200
        else:
            logging.warning(f"Project {project_id} not found.")
            return jsonify({'error': 'Project not found.'}), 404

    except Exception as e:
        logging.error(f"Error deleting project {project_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'An error occurred while deleting the project.'}), 500
    
@projects_bp.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get an individual project by its ID.
    """
    logging.info(f"Get Project called for ID: {project_id}")

    try:
        # Fetch the project from the database
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        
        if project:
            # Convert ObjectId to string and format the response
            project['id'] = str(project['_id'])
            del project['_id']  # Remove the original `_id` field
            logging.info(f"Project found: {project}")
            return jsonify(project), 200
        else:
            logging.warning(f"Project {project_id} not found.")
            return jsonify({'error': 'Project not found.'}), 404

    except Exception as e:
        logging.error(f"Error fetching project {project_id}: {str(e)}")
        return jsonify({'error': 'An error occurred while fetching the project.'}), 500

@projects_bp.route('/api/projects/<project_id>', methods=['PUT'])
def edit_project(project_id):
    """
    Edit an individual project by its ID.
    """
    logging.info(f"Edit Project called for ID: {project_id}")

    try:
        # Parse the request JSON
        update_data = request.json
        logging.info(f"Update data received: {update_data}")

        # Ensure data is valid
        if not update_data:
            logging.warning("No data provided for update.")
            return jsonify({'error': 'No data provided for update.'}), 400
        update_data.pop('id', None)  # Remove the `id` field if present
        
        # Update the project in the database
        result = db.projects.update_one(
            {'_id': ObjectId(project_id)},  # Match by ID
            {'$set': update_data}  # Update with new data
        )

        if result.matched_count == 1:
            if result.modified_count == 1:
                # Fetch the updated record
                updated_project = db.projects.find_one({'_id': ObjectId(project_id)})
                updated_project['id'] = str(updated_project['_id'])  # Convert ObjectId to string
                del updated_project['_id']  # Remove the original _id field

                logging.info(f"Project {project_id} successfully updated.")
                return jsonify(updated_project), 200  # Return updated project details
            else:
                logging.info(f"Project {project_id} not modified (data is the same).")
                return jsonify({'message': f'No changes made to project {project_id}.'}), 200
        else:
            logging.warning(f"Project {project_id} not found.")
            return jsonify({'error': 'Project not found.'}), 404

    except Exception as e:
        logging.error(f"Error updating project {project_id}: {str(e)}")
        return jsonify({'error': 'An error occurred while updating the project.'}), 500