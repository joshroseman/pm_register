import pandas as pd
import re

csv_path = "final_task_register.csv"
df = pd.read_csv(csv_path)

duplicates = df[df.duplicated("TaskID", keep=False)]
print(f"Found {len(duplicates)} rows with duplicate TaskIDs")

df.to_csv(f"{csv_path}.bak", index=False)
print(f"Created backup at {csv_path}.bak")


def generate_new_task_id(row_index, existing_ids):
    new_id = f"T{10000 + row_index}"
    while new_id in existing_ids:
        row_index += 1
        new_id = f"T{10000 + row_index}"
    return new_id


valid_task_ids = set()
for task_id in df["TaskID"]:
    if isinstance(task_id, str) and re.match(r"^T\d+$", task_id):
        valid_task_ids.add(task_id)

changes_made = 0
for idx, row in df.iterrows():
    task_id = row["TaskID"]

    is_duplicate = task_id in df.loc[: idx - 1, "TaskID"].values if idx > 0 else False
    is_invalid = not (isinstance(task_id, str) and re.match(r"^T\d+$", task_id))

    if is_duplicate or is_invalid:
        new_task_id = generate_new_task_id(idx, valid_task_ids)

        df.at[idx, "TaskID"] = new_task_id
        valid_task_ids.add(new_task_id)

        if pd.isna(row["TaskName"]) or (
            isinstance(row["TaskName"], str)
            and row["TaskName"].startswith(f"Task {task_id}")
        ):
            df.at[idx, "TaskName"] = f"Task {new_task_id}"

        changes_made += 1

        if changes_made % 20 == 0:
            print(f"Fixed {changes_made} TaskIDs so far...")

df.to_csv(csv_path, index=False)
print(f"Fixed {changes_made} duplicate or invalid TaskIDs")

duplicates_after = df[df.duplicated("TaskID", keep=False)]
print(f"Remaining duplicate TaskIDs: {len(duplicates_after)}")
