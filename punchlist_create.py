import os
import sys
import logging
import requests
import time
import datetime
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Devin_integrations', '.env')
load_dotenv(dotenv_path)

token = os.getenv('ASANA_ACCESS_TOKEN')
if not token:
    token = "2/3724152326817/1210268132218888:2df6b8221c51f3cab155966117340552"

base_url = "https://app.asana.com/api/1.0"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"
}

def punchlist_create(user_name="Josh Roseman", filter_date="06/06/2024"):
    """
    Create a private Asana project for the specified user with their incomplete tasks 
    that have due dates after the specified date.
    
    Args:
        user_name (str): Name of the user to create project for (default: "Josh Roseman")
        filter_date (str): Date string in MM/DD/YYYY format to filter tasks (default: "06/06/2024")
    
    Returns:
        tuple: (project_id, success_flag)
    """
    logger.info(f"Starting punchlist creation for {user_name}")
    
    try:
        try:
            filter_date_obj = datetime.strptime(filter_date, "%m/%d/%Y")
            logger.info(f"Filtering tasks due after {filter_date}")
        except ValueError:
            logger.error(f"Invalid date format: {filter_date}. Using default (no date filtering).")
            filter_date_obj = None
        
        workspaces_url = f"{base_url}/workspaces"
        workspaces_response = requests.get(workspaces_url, headers=headers)
        
        if workspaces_response.status_code != 200:
            logger.error(f"Failed to get workspaces: {workspaces_response.text}")
            return None, False
        
        workspaces = workspaces_response.json().get('data', [])
        loove_workspace = None
        
        logger.info("Available workspaces:")
        for workspace in workspaces:
            logger.info(f"ID: {workspace['gid']}, Name: {workspace['name']}")
            if "loove" in workspace['name'].lower():
                loove_workspace = workspace
                logger.info(f"Found Loove workspace: {workspace['name']} ({workspace['gid']})")
        
        if not loove_workspace:
            workspace_id = workspaces[0]['gid'] if workspaces else None
            logger.info(f"Loove workspace not found. Defaulting to first workspace: {workspaces[0]['name']} ({workspace_id})")
        else:
            workspace_id = loove_workspace['gid']
        
        users_url = f"{base_url}/workspaces/{workspace_id}/users"
        users_response = requests.get(users_url, headers=headers)
        
        if users_response.status_code != 200:
            logger.error(f"Failed to get users: {users_response.text}")
            return None, False
        
        users = users_response.json().get('data', [])
        target_user = None
        
        logger.info("Looking for user: " + user_name)
        for user in users:
            logger.info(f"User: {user['name']} (ID: {user['gid']})")
            if user_name.lower() in user['name'].lower():
                target_user = user
                logger.info(f"Found user: {user['name']} (ID: {user['gid']})")
                break
        
        if not target_user:
            logger.error(f"User {user_name} not found in workspace")
            return None, False
        
        teams_url = f"{base_url}/organizations/{workspace_id}/teams"
        teams_response = requests.get(teams_url, headers=headers)
        
        if teams_response.status_code != 200:
            logger.error(f"Failed to get teams: {teams_response.text}")
            teams_url = f"{base_url}/workspaces/{workspace_id}/teams"
            teams_response = requests.get(teams_url, headers=headers)
            
            if teams_response.status_code != 200:
                logger.error(f"Failed to get teams using alternative endpoint: {teams_response.text}")
                return None, False
        
        teams = teams_response.json().get('data', [])
        brain_team = None
        
        logger.info("Available teams:")
        for team in teams:
            logger.info(f"ID: {team['gid']}, Name: {team['name']}")
            if "brain" in team['name'].lower() or "ai" in team['name'].lower() or "boops" in team['name'].lower():
                brain_team = team
                logger.info(f"Found team: {team['name']} ({team['gid']})")
                break
        
        if not brain_team:
            team_id = teams[0]['gid'] if teams else None
            team_name = teams[0]['name'] if teams else "None"
            logger.info(f"Target team not found. Defaulting to first team: {team_name} ({team_id})")
        else:
            team_id = brain_team['gid']
        
        current_date = datetime.now().strftime("%m/%d")
        project_name = f"{user_name} punchlistery {current_date}"
        
        project_url = f"{base_url}/workspaces/{workspace_id}/projects"
        project_data = {
            "data": {
                "name": project_name,
                "public": False,  # Make it private to the user
                "notes": f"Punchlist for {user_name}. Contains incomplete tasks with due dates after {filter_date}.",
                "team": team_id
            }
        }
        
        project_response = requests.post(project_url, json=project_data, headers=headers)
        
        if project_response.status_code != 201:
            logger.error(f"Failed to create project: {project_response.text}")
            return None, False
        
        project = project_response.json().get('data', {})
        project_id = project.get('gid')
        
        logger.info(f"Created project '{project_name}' with ID: {project_id}")
        
        search_url = f"{base_url}/workspaces/{workspace_id}/tasks/search"
        search_params = {
            "assignee.any": target_user['gid'],
            "completed": False,  # Only get incomplete tasks
            "opt_fields": "name,due_on,completed,projects,notes"  # Include additional fields
        }
        
        search_response = requests.get(search_url, params=search_params, headers=headers)
        
        if search_response.status_code != 200:
            logger.error(f"Failed to search tasks: {search_response.text}")
            tasks_url = f"{base_url}/tasks"
            tasks_params = {
                "assignee": target_user['gid'],
                "workspace": workspace_id,
                "completed_since": "now",  # Only get incomplete tasks
                "opt_fields": "name,due_on,completed,projects,notes"
            }
            
            tasks_response = requests.get(tasks_url, params=tasks_params, headers=headers)
            
            if tasks_response.status_code != 200:
                logger.error(f"Failed to get tasks: {tasks_response.text}")
                return project_id, False
            
            tasks = tasks_response.json().get('data', [])
        else:
            tasks = search_response.json().get('data', [])
        
        logger.info(f"Found {len(tasks)} incomplete tasks assigned to {user_name}")
        
        filtered_tasks = []
        for task in tasks:
            if task.get('due_on'):
                task_due_date = datetime.strptime(task['due_on'], "%Y-%m-%d")
                if filter_date_obj and task_due_date >= filter_date_obj:
                    filtered_tasks.append(task)
            else:
                filtered_tasks.append(task)
        
        logger.info(f"Filtered to {len(filtered_tasks)} tasks with due dates after {filter_date} or no due date")
        
        successful_adds = 0
        for task in filtered_tasks:
            add_url = f"{base_url}/tasks/{task['gid']}/addProject"
            add_data = {
                "data": {
                    "project": project_id
                }
            }
            
            add_response = requests.post(add_url, json=add_data, headers=headers)
            
            if add_response.status_code == 200:
                logger.info(f"Added task '{task['name']}' to project")
                successful_adds += 1
            else:
                logger.error(f"Failed to add task to project: {add_response.text}")
        
        view_url = f"{base_url}/projects/{project_id}"
        view_data = {
            "data": {
                "default_view": "list",
                "view_settings": {
                    "sort_field": "due_date",
                    "sort_ascending": False  # False for newest at top
                }
            }
        }
        
        view_response = requests.put(view_url, json=view_data, headers=headers)
        
        if view_response.status_code == 200:
            logger.info("Set project view to list by due date (newest at top)")
        else:
            logger.warning(f"Failed to set project view: {view_response.text}")
            logger.warning("Project view may need to be configured manually")
        
        group_url = f"{base_url}/projects/{project_id}"
        group_data = {
            "data": {
                "view_settings": {
                    "group_field": "projects"  # Group by projects field
                }
            }
        }
        
        group_response = requests.put(group_url, json=group_data, headers=headers)
        
        if group_response.status_code == 200:
            logger.info("Set project to group tasks by project structure")
        else:
            logger.warning(f"Failed to set project grouping: {group_response.text}")
            logger.warning("Project grouping may need to be configured manually")
        
        logger.info("\nSummary:")
        logger.info(f"Created project '{project_name}' with ID: {project_id}")
        logger.info(f"Successfully added {successful_adds} of {len(filtered_tasks)} tasks to the project")
        logger.info(f"Project URL: https://app.asana.com/0/{project_id}/list")
        
        return project_id, successful_adds > 0
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None, False

if __name__ == "__main__":
    project_id, success = punchlist_create()
    if success:
        print(f"\nPunchlist created successfully! Access it at: https://app.asana.com/0/{project_id}/list")
    else:
        print("\nPunchlist creation encountered some issues. Check the logs for details.")
