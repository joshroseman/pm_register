import pandas as pd
import sys

try:
    df = pd.read_csv("final_task_register.csv")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    key_fields = [
        "TaskName",
        "TaskDescription",
        "Assignee",
        "Status",
        "ClassificationCategory",
        "IsInformationalContext",
        "TranscriptionMatchNotes",
    ]
    for field in key_fields:
        if field in df.columns:
            completeness = (df[field].notna() & (df[field] != "")).mean() * 100
            print(f"{field} completeness: {completeness:.2f}%")
        else:
            print(f"{field} not found in columns")

    if "ParentTaskID" in df.columns:
        parent_links = (
            df["ParentTaskID"].notna() & (df["ParentTaskID"] != "")
        ).mean() * 100
        print(f"ParentTaskID links: {parent_links:.2f}%")
    else:
        print("ParentTaskID not found in columns")

    if "SubTaskLevel" in df.columns:
        subtask_level = (
            df["SubTaskLevel"].notna() & (df["SubTaskLevel"] != "")
        ).mean() * 100
        print(f"SubTaskLevel population: {subtask_level:.2f}%")
    else:
        print("SubTaskLevel not found in columns")

    print("\nColumn names:")
    for col in df.columns:
        print(col)

except Exception as e:
    print(f"Error analyzing CSV: {e}")
    sys.exit(1)
