import pandas as pd

df = pd.read_csv("final_task_register.csv")

duplicates = df[df.duplicated("TaskID", keep=False)]
print(f"Found {len(duplicates)} rows with duplicate TaskIDs")
print("Sample of duplicate TaskIDs:")
print(duplicates["TaskID"].value_counts().head(10))

print("\nSample duplicate records:")
for task_id in duplicates["TaskID"].value_counts().head(3).index:
    print(f"\nDuplicate records for TaskID: {task_id}")
    dup_records = df[df["TaskID"] == task_id]
    for idx, row in dup_records.iterrows():
        print(f"Row {idx}: TaskName: {row['TaskName']}, Assignee: {row['Assignee']}")
