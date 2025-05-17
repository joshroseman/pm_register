import os
import sys
import logging
import requests
import time
import json
from requests.auth import HTTPBasicAuth
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

token = "2/3724152326817/1210268132218888:2df6b8221c51f3cab155966117340552"

base_url = "https://app.asana.com/api/1.0"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"
}

CUSTOM_FIELDS = [
    {
        "name": "Document Type",
        "type": "enum",
        "description": "Type of documentation",
        "enum_options": [
            {"name": "AI Integration"},
            {"name": "Business Structure"},
            {"name": "Financial"},
            {"name": "PM Register"},
            {"name": "Brand Guidelines"},
            {"name": "Technical"}
        ]
    },
    {
        "name": "Priority",
        "type": "enum",
        "description": "Document priority level",
        "enum_options": [
            {"name": "High"},
            {"name": "Medium"},
            {"name": "Low"}
        ]
    },
    {
        "name": "Format",
        "type": "enum",
        "description": "Document format",
        "enum_options": [
            {"name": "Markdown"},
            {"name": "CSV"},
            {"name": "RTF"},
            {"name": "DOCX"},
            {"name": "Other"}
        ]
    },
    {
        "name": "Assignee",
        "type": "text",
        "description": "Person responsible for maintaining this document"
    }
]

DOCUMENTATION_STRUCTURE = [
    {
        "name": "RASA-Manus Integration Plan",
        "notes": "Tactical implementation plan for integrating RASA and Manus",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/ai_integration/RASA-Manus_Integration_Tactical_Implementation_Plan.md",
        "custom_fields": {
            "Document Type": "AI Integration",
            "Priority": "High",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Ethical Considerations",
        "notes": "Analysis of ethical considerations for intimate interactions with intuitive AI models",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/ai_integration/Ethical_Considerations_of_Intimate_Interactions_with_Intuitive_AI_Models.md",
        "custom_fields": {
            "Document Type": "AI Integration",
            "Priority": "Medium",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "RASA Mirror Extension",
        "notes": "Technical details for RASA Mirror extension",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/ai_integration/RASA_Mirror_Extension_Snippet.md",
        "custom_fields": {
            "Document Type": "AI Integration",
            "Priority": "Medium",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    
    {
        "name": "Strategic Organization Summary",
        "notes": "Overview of LOOVE's multi-dimensional creative enterprise",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/business_structure/LOOVE_Annex_Strategic_Organization_Summary.md",
        "custom_fields": {
            "Document Type": "Business Structure",
            "Priority": "High",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Corp Structure",
        "notes": "LOOVE corporate structure information",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/business_structure/LOOVE_corp_structure.csv",
        "custom_fields": {
            "Document Type": "Business Structure",
            "Priority": "High",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Verticals by Division",
        "notes": "Vertical organization across divisions",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/business_structure/Verticals_by_division.csv",
        "custom_fields": {
            "Document Type": "Business Structure",
            "Priority": "Medium",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Divisions",
        "notes": "Division definitions and relationships",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/business_structure/Divisions.csv",
        "custom_fields": {
            "Document Type": "Business Structure",
            "Priority": "Medium",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Properties",
        "notes": "Property definitions and descriptions",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/business_structure/Properties.csv",
        "custom_fields": {
            "Document Type": "Business Structure",
            "Priority": "Medium",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Assets by Type",
        "notes": "Asset categorization and inventory",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/business_structure/Assets_by_type.csv",
        "custom_fields": {
            "Document Type": "Business Structure",
            "Priority": "Low",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Principal Property",
        "notes": "Principal property information",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/business_structure/Principal_property.csv",
        "custom_fields": {
            "Document Type": "Business Structure",
            "Priority": "Medium",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    
    {
        "name": "Q2 2025 Budget Initiative Planning",
        "notes": "Budget planning for Q2 2025 initiatives",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/financial/Q2_2025_budget_initiative_planning.csv",
        "custom_fields": {
            "Document Type": "Financial",
            "Priority": "High",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Weekly Projected Expenses Template",
        "notes": "Template for tracking weekly projected expenses and A/P",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/financial/Weekly_Projected_Expenses_Template.csv",
        "custom_fields": {
            "Document Type": "Financial",
            "Priority": "Medium",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Initiative Reporting",
        "notes": "Initiative-based financial reporting",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/financial/Initiative_reporting.csv",
        "custom_fields": {
            "Document Type": "Financial",
            "Priority": "Medium",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    
    {
        "name": "Asana Integration",
        "notes": "Documentation for PM Register's Asana integration",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/pm_register/ASANA_INTEGRATION_Original.md",
        "custom_fields": {
            "Document Type": "PM Register",
            "Priority": "High",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Task Initiatives Index",
        "notes": "Index of task initiatives",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/pm_register/PM_Task_Initiatives_Index.md",
        "custom_fields": {
            "Document Type": "PM Register",
            "Priority": "Medium",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Comparison Between Original and Improved PM Table Extraction",
        "notes": "Methodology analysis",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/pm_register/Comparison_Between_Original_and_Improved_PM_Table_Extraction.md",
        "custom_fields": {
            "Document Type": "PM Register",
            "Priority": "Medium",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Further PM Task Register Improvements Summary",
        "notes": "Summaries of improvements to the task register",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/pm_register/Further_PM_Task_Register_Improvements_Summary.md",
        "custom_fields": {
            "Document Type": "PM Register",
            "Priority": "Medium",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Advanced Improved Task Register",
        "notes": "Further improved task register CSV",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/pm_register/Advanced_Improved_Task_Register.csv",
        "custom_fields": {
            "Document Type": "PM Register",
            "Priority": "High",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Further Improved Task Register",
        "notes": "Further improved task register CSV",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/pm_register/Further_Improved_Task_Register.csv",
        "custom_fields": {
            "Document Type": "PM Register",
            "Priority": "High",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    
    {
        "name": "Unified LOOVE Style Guide",
        "notes": "Comprehensive style guide for LOOVE's brand identity",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/brand_guidelines/unified_loove_style_guide.md",
        "custom_fields": {
            "Document Type": "Brand Guidelines",
            "Priority": "High",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "LOOVE Brand Style Guide v1.5",
        "notes": "Comprehensive style guide for LOOVE's brand identity",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/brand_guidelines/Loove_Brand_Style_Guide_v1.5.md",
        "custom_fields": {
            "Document Type": "Brand Guidelines",
            "Priority": "High",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Sectors with Brand Architecture",
        "notes": "Sectors with brand architecture information",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/brand_guidelines/Sectors_with_brand_architecture.csv",
        "custom_fields": {
            "Document Type": "Brand Guidelines",
            "Priority": "Medium",
            "Format": "CSV",
            "Assignee": "Josh Roseman"
        }
    },
    
    {
        "name": "MTAP2 Containment Escalation Framework",
        "notes": "Framework for containment escalation",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/technical/MTAP2_Containment_Escalation_Framework.md",
        "custom_fields": {
            "Document Type": "Technical",
            "Priority": "High",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Invocation Shell Index & MTAP-1 Flare Logic Scaffold",
        "notes": "Technical documentation for invocation systems",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/technical/Invocation_Shell_Index_MTAP-1_Flare_Logic_Scaffold.md",
        "custom_fields": {
            "Document Type": "Technical",
            "Priority": "Medium",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "Shell Logic Thread Integrity Analysis",
        "notes": "Analysis of thread integrity in shell logic",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/technical/Shell_logic_THREAD_INTEGRITY_ANALYSIS.md",
        "custom_fields": {
            "Document Type": "Technical",
            "Priority": "Medium",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    },
    {
        "name": "LOOVE Brain Operational Cost/Benefit Analysis",
        "notes": "Analysis of operational costs and benefits",
        "file_path": "/home/ubuntu/repos/LooveDocumentation/technical/LOOVE_Brain_operational_cost_benefit_risk_analysis.md",
        "custom_fields": {
            "Document Type": "Technical",
            "Priority": "High",
            "Format": "Markdown",
            "Assignee": "Josh Roseman"
        }
    }
]

def get_or_create_custom_fields(workspace_id):
    """Get existing custom fields or create new ones in the workspace"""
    logger.info("Setting up custom fields in workspace")
    
    custom_fields_url = f"{base_url}/workspaces/{workspace_id}/custom_fields"
    custom_fields_response = requests.get(custom_fields_url, headers=headers)
    
    if custom_fields_response.status_code != 200:
        logger.error(f"Failed to get custom fields: {custom_fields_response.text}")
        return None
    
    existing_fields = custom_fields_response.json().get('data', [])
    existing_field_names = {field['name']: field for field in existing_fields}
    
    logger.info(f"Found {len(existing_fields)} existing custom fields in workspace")
    
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
        
        if field_def['type'] == 'enum' and 'enum_options' in field_def:
            field_data["data"]["enum_options"] = field_def['enum_options']
        
        create_field_response = requests.post(create_field_url, json=field_data, headers=headers)
        
        if create_field_response.status_code != 201:
            logger.error(f"Failed to create custom field '{field_def['name']}': {create_field_response.text}")
            continue
        
        new_field = create_field_response.json().get('data', {})
        custom_field_gids[field_def['name']] = new_field['gid']
        logger.info(f"Created new custom field '{field_def['name']}' with ID: {new_field['gid']}")
    
    return custom_field_gids

def upload_attachment(task_id, file_path):
    """Upload a file as an attachment to a task"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            
        file_name = os.path.basename(file_path)
        
        attachment_url = f"{base_url}/tasks/{task_id}/attachments"
        
        files = {
            'file': (file_name, file_content)
        }
        
        response = requests.post(
            attachment_url,
            headers={"Authorization": f"Bearer {token}"},
            files=files
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully uploaded attachment: {file_name}")
            return True
        else:
            logger.error(f"Failed to upload attachment: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error uploading attachment: {e}")
        return False

def create_project():
    """Create a documentation project in Asana mirroring the LooveDocumentation repository structure"""
    logger.info("Starting Asana project creation for LOOVE Documentation Mirror")
    
    try:
        workspaces_url = f"{base_url}/workspaces"
        workspaces_response = requests.get(workspaces_url, headers=headers)
        
        if workspaces_response.status_code != 200:
            logger.error(f"Failed to get workspaces: {workspaces_response.text}")
            return None, False
        
        workspaces_data = workspaces_response.json()
        workspaces = workspaces_data.get('data', [])
        loove_workspace = None
        
        logger.info("Available workspaces:")
        for workspace in workspaces:
            logger.info(f"ID: {workspace['gid']}, Name: {workspace['name']}")
            if "loove" in workspace['name'].lower():
                loove_workspace = workspace
                logger.info(f"Found LOOVE workspace: {workspace['name']} ({workspace['gid']})")
        
        if not loove_workspace:
            logger.info("LOOVE workspace not found. Please select a workspace ID from the list above.")
            
            workspace_id = workspaces[0]['gid'] if workspaces else None
            logger.info(f"Defaulting to first workspace: {workspaces[0]['name']} ({workspace_id})")
        else:
            workspace_id = loove_workspace['gid']
            logger.info(f"Using LOOVE workspace with ID: {workspace_id}")
        
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
        brain_team = None
        
        logger.info("Available teams:")
        for team in teams:
            logger.info(f"ID: {team['gid']}, Name: {team['name']}")
            if "brain" in team['name'].lower():
                brain_team = team
                logger.info(f"Found BRAIN team: {team['name']} ({team['gid']})")
        
        if not brain_team:
            logger.info("BRAIN AI werks team not found. Please select a team ID from the list above.")
            
            team_id = teams[0]['gid'] if teams else None
            logger.info(f"Defaulting to first team: {teams[0]['name'] if teams else 'None'} ({team_id})")
        else:
            team_id = brain_team['gid']
            logger.info(f"Using BRAIN AI werks team with ID: {team_id}")
        
        project_url = f"{base_url}/workspaces/{workspace_id}/projects"
        project_data = {
            "data": {
                "name": "LOOVE Documentation Mirror",
                "public": False,  # Make it private
                "notes": "Mirror of the LOOVE Documentation repository structure with all documentation files",
                "team": team_id
            }
        }
        
        project_response = requests.post(project_url, json=project_data, headers=headers)
        
        if project_response.status_code != 201:
            logger.error(f"Failed to create project: {project_response.text}")
            return None, False
        
        project = project_response.json().get('data', {})
        project_id = project.get('gid')
        
        logger.info(f"Created project 'LOOVE Documentation Mirror' with ID: {project_id}")
        
        logger.info(f"Adding custom field settings to project")
        for field_name, field_gid in custom_field_gids.items():
            settings_url = f"{base_url}/projects/{project_id}/custom_field_settings"
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
        
        logger.info("Waiting for custom fields to be properly associated with the project...")
        time.sleep(5)  # Increased wait time to ensure custom fields are properly associated
        
        successful_tasks = 0
        successful_attachments = 0
        
        for task_data in DOCUMENTATION_STRUCTURE:
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
                
                if 'file_path' in task_data and os.path.exists(task_data['file_path']):
                    if upload_attachment(task_id, task_data['file_path']):
                        successful_attachments += 1
                
                if 'custom_fields' in task_data:
                    
                    project_fields_url = f"{base_url}/projects/{project_id}/custom_field_settings"
                    project_fields_response = requests.get(project_fields_url, headers=headers)
                    
                    if project_fields_response.status_code != 200:
                        logger.warning(f"Failed to get project custom fields: {project_fields_response.text}")
                        continue
                    
                    project_fields = project_fields_response.json().get('data', [])
                    project_field_gids = {}
                    
                    for field in project_fields:
                        field_data = field.get('custom_field', {})
                        field_name_from_api = field_data.get('name')
                        field_gid_from_api = field_data.get('gid')
                        
                        if field_name_from_api:
                            project_field_gids[field_name_from_api] = field_gid_from_api
                            logger.info(f"Project has custom field: {field_name_from_api} with GID: {field_gid_from_api}")
                    
                    custom_fields_data = {}
                    
                    for field_name, field_value in task_data['custom_fields'].items():
                        if field_name in project_field_gids and field_value:
                            field_gid = project_field_gids[field_name]
                            
                            if field_name in ['Document Type', 'Priority', 'Format']:
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
                                        custom_fields_data[field_gid] = option['gid']
                                        found_option = True
                                        logger.info(f"Found enum option '{field_value}' with GID: {option['gid']}")
                                        break
                                
                                if not found_option:
                                    logger.warning(f"Could not find enum option '{field_value}' for field '{field_name}'. Available options: {[o['name'] for o in enum_options]}")
                            else:
                                custom_fields_data[field_gid] = field_value
                    
                    if custom_fields_data:
                        update_task_url = f"{base_url}/tasks/{task_id}"
                        update_data = {
                            "data": {
                                "custom_fields": custom_fields_data
                            }
                        }
                        
                        update_response = requests.put(update_task_url, json=update_data, headers=headers)
                        
                        if update_response.status_code == 200:
                            logger.info(f"Set custom field values for task: {custom_fields_data}")
                        else:
                            logger.warning(f"Failed to set custom field values: {update_response.text}")
            
            except Exception as e:
                logger.error(f"Error creating task '{task_data['name']}': {e}")
                continue
        
        logger.info("\nSummary:")
        logger.info(f"Created project 'LOOVE Documentation Mirror' in workspace")
        logger.info(f"Successfully added {successful_tasks} of {len(DOCUMENTATION_STRUCTURE)} tasks to the project")
        logger.info(f"Successfully uploaded {successful_attachments} of {len(DOCUMENTATION_STRUCTURE)} attachments")
        logger.info(f"Custom fields used: {', '.join(custom_field_gids.keys())}")
        logger.info(f"Project URL: https://app.asana.com/0/{project_id}/list")
        
        return project_id, successful_tasks == len(DOCUMENTATION_STRUCTURE)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None, False

if __name__ == "__main__":
    project_id, success = create_project()
    if success:
        print(f"\nDocumentation mirror project created successfully! Access it at: https://app.asana.com/0/{project_id}/list")
    else:
        print("\nProject creation encountered some issues. Check the logs for details.")
