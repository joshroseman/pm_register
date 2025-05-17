# Asana Integration for PM Register

This document outlines the process of integrating the PM Register with Asana, enabling task data to be synchronized between the GitHub-based PM Register system and Asana's project management platform.

## Overview

The PM Register can be exported to Asana as a project with custom fields that mirror the structure and metadata of the CSV-based task register. This integration provides teams with the ability to:

1. View and manage tasks in Asana's visual interface
2. Leverage Asana's collaboration features while maintaining the PM Register as the source of truth
3. Organize tasks using the same hierarchical structure (Initiative > Project > Task)
4. Maintain consistent metadata across platforms (Vertical, Priority, Effort Estimate, etc.)

## Custom Fields Structure

The integration creates the following custom fields in Asana to maintain consistency with the PM Register:

| Field Name     | Type   | Description                                      |
|----------------|--------|--------------------------------------------------|
| TaskID         | Text   | Unique identifier for tasks in PM register       |
| Initiative     | Enum   | Strategic initiative the task belongs to         |
| Project        | Enum   | Project category within the initiative           |
| Vertical       | Enum   | Department or functional area                    |
| PriorityBand   | Enum   | Task priority level                              |
| EffortEstimate | Enum   | Estimated effort required                        |

## Integration Scripts

The repository contains two scripts for Asana integration:

1. `create_asana_project.py` - Creates a project for Retail Operations tasks only
2. `import_full_register_to_asana.py` - Creates a project for the full PM task register

### Script Functionality

Both scripts perform the following operations:

1. Read task data (from JSON or CSV)
2. Extract unique values for enum fields
3. Create custom fields in Asana (or use existing ones)
4. Create a new project in the specified workspace and team
5. Import tasks with their metadata
6. Associate custom field values with tasks

## Prerequisites

- Asana Personal Access Token
- Python 3.6+
- Required Python packages: `requests`

## Usage

To import the full PM task register to Asana:

```bash
python import_full_register_to_asana.py
```

## Hierarchical Structure

The PM Register's hierarchical structure is represented in Asana through custom fields:

- **Initiative**: Strategic goal/project (e.g., Facility Maintenance, RASA Operations)
- **Project**: Category within an initiative (e.g., Building Repairs, RASA Management)
- **Task**: Individual task with metadata

## Limitations

- Task assignments are not included in the current import process
- Task relationships (parent-child, blocking) are not represented in Asana
- Changes made in Asana are not automatically synchronized back to the PM Register

## Future Enhancements

Potential future enhancements to the integration:

1. Bi-directional synchronization between PM Register and Asana
2. Support for task relationships and dependencies
3. Integration with Asana's timeline and portfolio features
4. Automated regular sync via GitHub Actions workflow

## Repository Configuration

The Asana integration uses the following repositories and configuration files:

1. **PM Register Repository** (`joshroseman/pm_register`):
   - Integration scripts: `create_asana_project.py`, `import_full_register_to_asana.py`, `create_documentation_project.py`
   - Documentation: `ASANA_INTEGRATION.md` (this file)
   - Task data: `final_task_register.csv`

2. **Devin Integrations Repository** (`joshroseman/Devin_integrations`):
   - Asana API token located in `.env` file
   - Node.js integration for Asana API

## Asana Workspace Configuration

The Asana integration uses the following Asana workspace and team:

- **Workspace**: "loove labs" (ID: 2943879779347)
- **Team**: "Boops / retail" (ID: 1203161769284845)
- **AI/BRAIN Team Space**: Located in the "loove labs" workspace
- **Documentation Project**: [PM Register Documentation](https://app.asana.com/0/1210281698138647/list)

## Related Documentation

For additional context and information about the business structure, see the Loove Documentation repository, which contains:

- Business structure information
- Financial planning documents
- Brand guidelines
- AI integration documentation
- Technical frameworks

The repository is organized into logical subdirectories for easy navigation.
