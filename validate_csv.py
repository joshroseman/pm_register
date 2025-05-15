import pandas as pd
import sys

try:
    df = pd.read_csv("final_task_register.csv")
    print(f"Successfully loaded CSV with {len(df)} rows")

    required_columns = [
        "TaskID",
        "TaskName",
        "TaskDescription",
        "Assignee",
        "Initiative",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        sys.exit(1)

    empty_tasks = df[df["TaskName"].isna() | df["TaskName"] == ""]
    if not empty_tasks.empty:
        print(f"Warning: Found {len(empty_tasks)} tasks with empty names")

    duplicates = df[df.duplicated("TaskID", keep=False)]
    if not duplicates.empty:
        print(f"Error: Found {len(duplicates)} duplicate task IDs")
        sys.exit(1)

    print("Validation completed successfully")

except Exception as e:
    print(f"Error validating CSV: {e}")
    sys.exit(1)
