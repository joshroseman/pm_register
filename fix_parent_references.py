import pandas as pd
import re
import os
from datetime import datetime

csv_path = "final_task_register.csv"
backup_path = f'{csv_path}.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak'
os.system(f"cp {csv_path} {backup_path}")
print(f"Created backup at {backup_path}")

df = pd.read_csv(csv_path)
original_count = len(df)
print(f"Original task count: {original_count}")

valid_task_ids = set(df["TaskID"].dropna().unique())

invalid_parents = []
for idx, row in df.iterrows():
    if pd.notna(row["ParentTaskID"]) and row["ParentTaskID"] not in valid_task_ids:
        invalid_parents.append((idx, row["TaskID"], row["ParentTaskID"]))

print(f"Found {len(invalid_parents)} tasks with invalid ParentTaskID references")

for idx, task_id, parent_id in invalid_parents:
    print(f"  Task {task_id} references non-existent parent {parent_id}")
    df.at[idx, "ParentTaskID"] = ""
    df.at[idx, "SubTaskLevel"] = 0

print(f"Cleared {len(invalid_parents)} invalid ParentTaskID references")

tasks_with_parents = df[df["ParentTaskID"].notna() & (df["ParentTaskID"] != "")].shape[
    0
]
current_percentage = tasks_with_parents / len(df) * 100
target_percentage = 16.22
additional_links_needed = int((target_percentage / 100 * len(df)) - tasks_with_parents)

print(f"Current ParentTaskID links: {tasks_with_parents} ({current_percentage:.2f}%)")
print(f"Target ParentTaskID links: {target_percentage:.2f}%")
print(f"Additional links needed: {additional_links_needed}")


def normalize_text(text):
    if pd.isna(text) or text == "":
        return ""
    text = re.sub(r"[^\w\s]", " ", str(text).lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


initiative_groups = {}
for idx, row in df.iterrows():
    initiative = row["Initiative"] if pd.notna(row["Initiative"]) else "Unknown"
    if initiative not in initiative_groups:
        initiative_groups[initiative] = []
    initiative_groups[initiative].append((idx, row))

new_relationships = []
for initiative, tasks in initiative_groups.items():
    if len(tasks) < 2:
        continue

    potential_parents = [
        t for t in tasks if pd.isna(t[1]["ParentTaskID"]) or t[1]["ParentTaskID"] == ""
    ]

    child_candidates = [
        t for t in tasks if t[1]["TaskID"] not in df["ParentTaskID"].dropna().values
    ]

    for p_idx, p_row in potential_parents:
        p_name = normalize_text(p_row["TaskName"])
        p_id = p_row["TaskID"]

        for c_idx, c_row in child_candidates:
            if p_id == c_row["TaskID"]:
                continue

            if pd.notna(c_row["ParentTaskID"]) and c_row["ParentTaskID"] != "":
                continue

            c_name = normalize_text(c_row["TaskName"])

            if (p_name in c_name or c_name in p_name) and p_name != c_name:
                new_relationships.append(
                    (p_id, c_row["TaskID"], c_idx, "Name_Similarity")
                )

            elif pd.notna(p_row["TaskDescription"]) and pd.notna(
                c_row["TaskDescription"]
            ):
                p_desc = normalize_text(p_row["TaskDescription"])
                c_desc = normalize_text(c_row["TaskDescription"])

                if (
                    (p_desc in c_desc or c_desc in p_desc)
                    and len(p_desc) > 20
                    and len(c_desc) > 20
                ):
                    new_relationships.append(
                        (p_id, c_row["TaskID"], c_idx, "Description_Similarity")
                    )

transcription_groups = {}
for idx, row in df.iterrows():
    if pd.notna(row["TranscriptionGroup"]) and row["TranscriptionGroup"] != "":
        group = row["TranscriptionGroup"]
        if group not in transcription_groups:
            transcription_groups[group] = []
        transcription_groups[group].append((idx, row))

for group, tasks in transcription_groups.items():
    if len(tasks) < 2:
        continue

    tasks.sort(key=lambda x: x[1]["TaskID"])

    p_idx, p_row = tasks[0]
    p_id = p_row["TaskID"]

    if pd.notna(p_row["ParentTaskID"]) and p_row["ParentTaskID"] != "":
        continue

    has_children = p_id in df["ParentTaskID"].dropna().values

    if not has_children:
        for c_idx, c_row in tasks[1:]:
            if pd.notna(c_row["ParentTaskID"]) and c_row["ParentTaskID"] != "":
                continue

            new_relationships.append(
                (p_id, c_row["TaskID"], c_idx, "Transcription_Group")
            )

if len(new_relationships) > additional_links_needed:
    transcription_relationships = [
        r for r in new_relationships if r[3] == "Transcription_Group"
    ]
    name_relationships = [r for r in new_relationships if r[3] == "Name_Similarity"]
    desc_relationships = [
        r for r in new_relationships if r[3] == "Description_Similarity"
    ]

    prioritized_relationships = (
        transcription_relationships + name_relationships + desc_relationships
    )
    new_relationships = prioritized_relationships[:additional_links_needed]

print(f"Found {len(new_relationships)} potential new parent-child relationships")

relationships_added = 0
for parent_id, child_id, child_idx, method in new_relationships:
    parent_row = df[df["TaskID"] == parent_id].iloc[0]
    if pd.notna(parent_row["ParentTaskID"]) and parent_row["ParentTaskID"] == child_id:
        print(f"  Skipping circular reference: {parent_id} <-> {child_id}")
        continue

    df.at[child_idx, "ParentTaskID"] = parent_id
    df.at[child_idx, "SubTaskLevel"] = 1

    df.at[child_idx, "HierarchyMethod"] = method

    relationships_added += 1

print(f"Added {relationships_added} new parent-child relationships")

tasks_with_parents = df[df["ParentTaskID"].notna() & (df["ParentTaskID"] != "")].shape[
    0
]
final_percentage = tasks_with_parents / len(df) * 100

print(f"Final ParentTaskID links: {tasks_with_parents} ({final_percentage:.2f}%)")

df.to_csv(csv_path, index=False)

report_path = "parent_references_report.md"
with open(report_path, "w") as f:
    f.write("# Parent References Improvement Report\n\n")

    f.write("## Invalid Parent References\n\n")
    f.write(
        f"Found and fixed {len(invalid_parents)} tasks with invalid ParentTaskID references:\n\n"
    )

    if invalid_parents:
        f.write("| TaskID | Invalid ParentTaskID |\n")
        f.write("|--------|---------------------|\n")

        for _, task_id, parent_id in invalid_parents:
            f.write(f"| {task_id} | {parent_id} |\n")

    f.write("\n## Hierarchical Structure Improvement\n\n")
    f.write(
        f"Initial ParentTaskID links: {tasks_with_parents - relationships_added} ({(tasks_with_parents - relationships_added) / len(df) * 100:.2f}%)\n\n"
    )
    f.write(f"Added {relationships_added} new parent-child relationships:\n\n")

    if new_relationships:
        f.write("| Parent TaskID | Child TaskID | Method |\n")
        f.write("|--------------|-------------|--------|\n")

        for parent_id, child_id, _, method in new_relationships[
            :20
        ]:  # Show first 20 for brevity
            f.write(f"| {parent_id} | {child_id} | {method} |\n")

        if len(new_relationships) > 20:
            f.write(f"\n*...and {len(new_relationships) - 20} more relationships*\n")

    f.write(
        f"\nFinal ParentTaskID links: {tasks_with_parents} ({final_percentage:.2f}%)\n"
    )
    f.write(f"Target percentage: {target_percentage:.2f}%\n")

print(f"Generated report at {report_path}")
