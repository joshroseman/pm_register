import asana
import json
import os
import sys
import logging
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

with open('retail_operations_asana_import.json', 'r') as f:
    tasks = json.load(f)

token = "2/3724152326817/1210268132218888:2df6b8221c51f3cab155966117340552"

base_url = "https://app.asana.com/api/1.0"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"
}

CUSTOM_FIELDS = [
    {
        "name": "TaskID",
        "type": "text",
        "description": "Unique identifier for tasks in PM register"
    },
    {
        "name": "Initiative",
        "type": "text",
        "description": "Strategic initiative the task belongs to"
    },
    {
        "name": "Vertical",
        "type": "enum",
        "description": "Department or functional area",
        "enum_options": []  # Will be populated dynamically
    },
    {
        "name": "EffortEstimate",
        "type": "enum",
        "description": "Estimated effort required",
        "enum_options": []  # Will be populated dynamically
    },
    {
        "name": "PriorityBand",
        "type": "enum",
        "description": "Task priority level",
        "enum_options": []  # Will be populated dynamically
    }
]

def get_or_create_custom_fields(workspace_id):
    """Get existing custom fields or create new ones in the workspace"""
    logger.info("Setting up custom fields in workspace")
    
    # Get existing custom fields in the workspace
    custom_fields_url = f"{base_url}/workspaces/{workspace_id}/custom_fields"
    custom_fields_response = requests.get(custom_fields_url, headers=headers)
    
    if custom_fields_response.status_code != 200:
        logger.error(f"Failed to get custom fields: {custom_fields_response.text}")
        return None
    
    existing_fields = custom_fields_response.json().get('data', [])
    existing_field_names = {field['name']: field for field in existing_fields}
    
    logger.info(f"Found {len(existing_fields)} existing custom fields in workspace")
    
    verticals = set()
    effort_estimates = set()
    priorities = set()
    
    for task in tasks:
        if 'custom_fields' in task:
            if 'Vertical' in task['custom_fields'] and task['custom_fields']['Vertical']:
                verticals.add(task['custom_fields']['Vertical'])
            if 'EffortEstimate' in task['custom_fields'] and task['custom_fields']['EffortEstimate']:
                effort_estimates.add(task['custom_fields']['EffortEstimate'])
            if 'PriorityBand' in task['custom_fields'] and task['custom_fields']['PriorityBand']:
                priorities.add(task['custom_fields']['PriorityBand'])
    
    for field in CUSTOM_FIELDS:
        if field['name'] == 'Vertical':
            field['enum_options'] = [{"name": v} for v in verticals if v]
        elif field['name'] == 'EffortEstimate':
            field['enum_options'] = [{"name": e} for e in effort_estimates if e]
        elif field['name'] == 'PriorityBand':
            field['enum_options'] = [{"name": p} for p in priorities if p]
    
    custom_field_gids = {}
    
    for field_def in CUSTOM_FIELDS:
        if field_def['name'] in existing_field_names:
            field = existing_field_names[field_def['name']]
            custom_field_gids[field_def['name']] = field['gid']
            logger.info(f"Using existing custom field '{field_def['name']}' with ID: {field['gid']}")
            continue
        
        create_field_url = f"{base_url}/custom_fields"
        field_data = {
            "data": {
                "workspace": workspace_id,
                "name": field_def['name'],
                "resource_subtype": field_def['type'],
                "description": field_def['description'],
                "enabled": True,
                "is_global_to_workspace": True
            }
        }
        
        if field_def['type'] == 'enum' and field_def['enum_options']:
            field_data["data"]["enum_options"] = field_def['enum_options']
        
        create_field_response = requests.post(create_field_url, json=field_data, headers=headers)
        
        if create_field_response.status_code != 201:
            logger.error(f"Failed to create custom field '{field_def['name']}': {create_field_response.text}")
            continue
        
        new_field = create_field_response.json().get('data', {})
        custom_field_gids[field_def['name']] = new_field['gid']
        logger.info(f"Created new custom field '{field_def['name']}' with ID: {new_field['gid']}")
    
    return custom_field_gids

def create_project():
    """Create a private project in the BOOPS team for Retail Operations initiative"""
    logger.info("Starting Asana project creation for Retail Operations")
    
    try:
        workspaces_url = f"{base_url}/workspaces"
        workspaces_response = requests.get(workspaces_url, headers=headers)
        
        if workspaces_response.status_code != 200:
            logger.error(f"Failed to get workspaces: {workspaces_response.text}")
            return None, False
        
        workspaces_data = workspaces_response.json()
        workspaces = workspaces_data.get('data', [])
        boops_workspace = None
        
        logger.info("Available workspaces:")
        for workspace in workspaces:
            logger.info(f"ID: {workspace['gid']}, Name: {workspace['name']}")
            if "boops" in workspace['name'].lower():
                boops_workspace = workspace
                logger.info(f"Found BOOPS workspace: {workspace['name']} ({workspace['gid']})")
        
        if not boops_workspace:
            logger.info("BOOPS workspace not found. Please select a workspace ID from the list above.")
            
            workspace_id = workspaces[0]['gid'] if workspaces else None
            logger.info(f"Defaulting to first workspace: {workspaces[0]['name']} ({workspace_id})")
        else:
            workspace_id = boops_workspace['gid']
            logger.info(f"Using BOOPS workspace with ID: {workspace_id}")
        
        # Set up custom fields in workspace
        custom_field_gids = get_or_create_custom_fields(workspace_id)
        if not custom_field_gids:
            logger.error("Failed to set up custom fields")
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
        boops_team = None
        
        logger.info("Available teams:")
        for team in teams:
            logger.info(f"ID: {team['gid']}, Name: {team['name']}")
            if "boops" in team['name'].lower():
                boops_team = team
                logger.info(f"Found BOOPS team: {team['name']} ({team['gid']})")
        
        if not boops_team:
            logger.info("BOOPS team not found. Please select a team ID from the list above.")
            
            team_id = teams[0]['gid'] if teams else None
            logger.info(f"Defaulting to first team: {teams[0]['name'] if teams else 'None'} ({team_id})")
        else:
            team_id = boops_team['gid']
            logger.info(f"Using BOOPS team with ID: {team_id}")
        
        # Create a new project in the selected workspace and team
        project_url = f"{base_url}/workspaces/{workspace_id}/projects"
        project_data = {
            "data": {
                "name": "Retail Operations",
                "public": False,  # Make it private
                "notes": "Project for Retail Operations initiative tasks from PM register",
                "team": team_id
            }
        }
        
        project_response = requests.post(project_url, json=project_data, headers=headers)
        
        if project_response.status_code != 201:
            logger.error(f"Failed to create project: {project_response.text}")
            return None, False
        
        project = project_response.json().get('data', {})
        project_id = project.get('gid')
        
        logger.info(f"Created project 'Retail Operations' with ID: {project_id}")
        
        logger.info(f"Adding custom field settings to project")
        for field_name, field_gid in custom_field_gids.items():
            settings_url = f"{base_url}/projects/{project_id}/add_custom_field_setting"
            settings_data = {
                "data": {
                    "custom_field": field_gid,
                    "is_important": True
                }
            }
            
            settings_response = requests.post(settings_url, json=settings_data, headers=headers)
            
            if settings_response.status_code != 200:
                logger.warning(f"Failed to add custom field '{field_name}' to project: {settings_response.text}")
                continue
            
            logger.info(f"Added custom field '{field_name}' to project")
        
        import time
        time.sleep(2)  # Wait for 2 seconds
        
        successful_tasks = 0
        for task_data in tasks:
            try:
                task_payload = {
                    "data": {
                        "name": task_data['name'],
                        "notes": task_data['notes'],
                        "projects": [project_id],  # Add to our new project
                        "workspace": workspace_id
                    }
                }
                
                task_url = f"{base_url}/tasks"
                task_response = requests.post(task_url, json=task_payload, headers=headers)
                
                if task_response.status_code != 201:
                    logger.error(f"Failed to create task: {task_response.text}")
                    continue
                
                task = task_response.json().get('data', {})
                task_id = task.get('gid')
                
                logger.info(f"Created task '{task_data['name']}' with ID: {task_id}")
                successful_tasks += 1
                
                if 'custom_fields' in task_data:
                    for field_name, field_value in task_data['custom_fields'].items():
                        if field_name in custom_field_gids and field_value:
                            field_gid = custom_field_gids[field_name]
                            
                            update_task_url = f"{base_url}/tasks/{task_id}"
                            update_data = {
                                "data": {
                                    "custom_fields": {
                                        field_gid: field_value
                                    }
                                }
                            }
                            
                            if field_name in ['Vertical', 'EffortEstimate', 'PriorityBand']:
                                field_url = f"{base_url}/custom_fields/{field_gid}"
                                field_response = requests.get(field_url, headers=headers)
                                
                                if field_response.status_code != 200:
                                    logger.warning(f"Failed to get custom field details: {field_response.text}")
                                    continue
                                
                                field_details = field_response.json().get('data', {})
                                enum_options = field_details.get('enum_options', [])
                                
                                found_option = False
                                for option in enum_options:
                                    if option['name'] == field_value:
                                        update_data['data']['custom_fields'][field_gid] = option['gid']
                                        found_option = True
                                        logger.info(f"Found enum option '{field_value}' with GID: {option['gid']}")
                                        break
                                
                                if not found_option:
                                    logger.warning(f"Could not find enum option '{field_value}' for field '{field_name}'. Available options: {[o['name'] for o in enum_options]}")
                                    continue
                            
                            update_response = requests.put(update_task_url, json=update_data, headers=headers)
                            
                            if update_response.status_code == 200:
                                logger.info(f"Set '{field_name}' to '{field_value}' for task")
                            else:
                                logger.warning(f"Failed to set custom field value: {update_response.text}")
                
                if task_data['assignee']:
                    try:
                        # Get users in workspace
                        users_url = f"{base_url}/workspaces/{workspace_id}/users"
                        users_response = requests.get(users_url, headers=headers)
                        
                        if users_response.status_code != 200:
                            logger.warning(f"Failed to get users: {users_response.text}")
                            continue
                        
                        users = users_response.json().get('data', [])
                        assignee = None
                        
                        for user in users:
                            if task_data['assignee'].lower() in user['name'].lower():
                                assignee = user
                                break
                        
                        if assignee:
                            update_task_url = f"{base_url}/tasks/{task_id}"
                            update_payload = {
                                "data": {
                                    "assignee": assignee['gid']
                                }
                            }
                            
                            update_response = requests.put(update_task_url, json=update_payload, headers=headers)
                            
                            if update_response.status_code == 200:
                                logger.info(f"Assigned task to {assignee['name']}")
                            else:
                                logger.warning(f"Failed to assign task: {update_response.text}")
                        else:
                            logger.warning(f"Could not find user '{task_data['assignee']}' to assign task")
                    
                    except Exception as e:
                        logger.warning(f"Error assigning task: {e}")
            
            except Exception as e:
                logger.error(f"Error creating task '{task_data['name']}': {e}")
                continue
        
        logger.info("\nSummary:")
        logger.info(f"Created project 'Retail Operations' in workspace")
        logger.info(f"Successfully added {successful_tasks} of {len(tasks)} tasks to the project")
        logger.info(f"Custom fields used instead of tags: {', '.join(custom_field_gids.keys())}")
        logger.info(f"Project URL: https://app.asana.com/0/{project_id}/list")
        
        return project_id, successful_tasks == len(tasks)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None, False

if __name__ == "__main__":
    project_id, success = create_project()
    if success:
        print(f"\nProject created successfully! Access it at: https://app.asana.com/0/{project_id}/list")
    else:
        print("\nProject creation encountered some issues. Check the logs for details.")
