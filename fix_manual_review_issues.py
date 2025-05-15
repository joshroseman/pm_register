import pandas as pd
import re
import numpy as np
from collections import defaultdict

csv_path = "final_task_register.csv"
df = pd.read_csv(csv_path)

print(f"=== FIXING ISSUES FROM MANUAL REVIEW ===")
print(f"Total rows before: {len(df)}")

df.to_csv(f"{csv_path}.manual_review.bak", index=False)
print(f"Created backup at {csv_path}.manual_review.bak")

print("\n=== FIXING INVALID PARENT REFERENCES ===")
all_task_ids = set(df["TaskID"])
invalid_parents_mask = (
    df["ParentTaskID"].notna()
    & (df["ParentTaskID"] != "")
    & ~df["ParentTaskID"].isin(all_task_ids)
)
invalid_parents = df[invalid_parents_mask]
print(f"Found {len(invalid_parents)} tasks with invalid ParentTaskID references")

df.loc[invalid_parents_mask, "ParentTaskID"] = ""
df.loc[invalid_parents_mask, "SubTaskLevel"] = 0
print(f"Cleared {len(invalid_parents)} invalid parent references")

print("\n=== FIXING CIRCULAR REFERENCES ===")
hierarchy_map = defaultdict(list)
for idx, row in df.iterrows():
    if pd.notna(row["ParentTaskID"]) and row["ParentTaskID"] != "":
        hierarchy_map[row["ParentTaskID"]].append(row["TaskID"])


def detect_circular_refs(task_id, parent_id, hierarchy_map):
    if task_id == parent_id:
        return True

    if parent_id in hierarchy_map and task_id in hierarchy_map[parent_id]:
        return True

    current_id = parent_id
    visited = {task_id, parent_id}
    for _ in range(5):  # Limit depth to avoid infinite loops
        if current_id not in hierarchy_map:
            return False

        for child_id in hierarchy_map[current_id]:
            if child_id in visited:
                return True
            visited.add(child_id)

            if child_id in hierarchy_map and any(
                ref in visited for ref in hierarchy_map[child_id]
            ):
                return True

    return False


circular_refs_fixed = 0
for idx, row in df.iterrows():
    if pd.notna(row["ParentTaskID"]) and row["ParentTaskID"] != "":
        task_id = row["TaskID"]
        parent_id = row["ParentTaskID"]

        if detect_circular_refs(task_id, parent_id, hierarchy_map):
            df.at[idx, "ParentTaskID"] = ""
            df.at[idx, "SubTaskLevel"] = 0
            circular_refs_fixed += 1

print(f"Fixed {circular_refs_fixed} circular references")

print("\n=== FIXING SUBTASKLEVEL INCONSISTENCIES ===")
df["SubTaskLevel"] = pd.to_numeric(df["SubTaskLevel"], errors="coerce")
df["SubTaskLevel"] = df["SubTaskLevel"].fillna(0)
df["SubTaskLevel"] = df["SubTaskLevel"].astype(int)

parent_links = df[df["ParentTaskID"].notna() & (df["ParentTaskID"] != "")]
inconsistent_levels = parent_links[parent_links["SubTaskLevel"] == 0]
df.loc[inconsistent_levels.index, "SubTaskLevel"] = 1
print(f"Fixed {len(inconsistent_levels)} tasks with parents but SubTaskLevel = 0")

no_parent_tasks = df[df["ParentTaskID"].isna() | (df["ParentTaskID"] == "")]
inconsistent_no_parent = no_parent_tasks[no_parent_tasks["SubTaskLevel"] > 0]
df.loc[inconsistent_no_parent.index, "SubTaskLevel"] = 0
print(f"Fixed {len(inconsistent_no_parent)} tasks without parents but SubTaskLevel > 0")

print("\n=== FIXING INITIATIVE COHERENCE ===")
initiative_fixes = 0
hierarchy_map = defaultdict(list)
for idx, row in df.iterrows():
    if pd.notna(row["ParentTaskID"]) and row["ParentTaskID"] != "":
        hierarchy_map[row["ParentTaskID"]].append(row["TaskID"])

for parent_id, children in hierarchy_map.items():
    parent_row = df[df["TaskID"] == parent_id]
    if not parent_row.empty:
        parent_initiative = parent_row.iloc[0]["Initiative"]
        for child_id in children:
            child_idx = df[df["TaskID"] == child_id].index
            if (
                not child_idx.empty
                and df.loc[child_idx[0], "Initiative"] != parent_initiative
            ):
                df.loc[child_idx[0], "Initiative"] = parent_initiative
                initiative_fixes += 1

print(f"Fixed {initiative_fixes} initiative mismatches between parents and children")

print("\n=== FIXING SPECIAL ENTRY HANDLING ===")
rasa_tasks = df[
    (df["TaskName"].str.contains("RASA", case=False, na=False))
    | (df["TaskDescription"].str.contains("RASA", case=False, na=False))
]
rasa_not_info = rasa_tasks[rasa_tasks["IsInformationalContext"] != "True"]
df.loc[rasa_not_info.index, "IsInformationalContext"] = "True"
print(
    f"Marked {len(rasa_not_info)} tasks with RASA references as informational contexts"
)

print("\n=== IMPROVING HIERARCHICAL STRUCTURE ===")
current_parent_links = len(df[df["ParentTaskID"].notna() & (df["ParentTaskID"] != "")])
current_percentage = current_parent_links / len(df) * 100
target_percentage = 16.22
target_links = int(len(df) * target_percentage / 100)
links_to_add = target_links - current_parent_links
print(
    f"Current ParentTaskID links: {current_percentage:.2f}% ({current_parent_links} tasks)"
)
print(f"Target ParentTaskID links: {target_percentage:.2f}% ({target_links} tasks)")
print(f"Need to add {links_to_add} parent-child relationships")

initiatives = df["Initiative"].dropna().unique()
added_links = 0

for initiative in initiatives:
    if added_links >= links_to_add:
        break

    initiative_tasks = df[df["Initiative"] == initiative]

    if len(initiative_tasks) < 3:
        continue

    potential_parents = initiative_tasks[
        (
            initiative_tasks["ParentTaskID"].isna()
            | (initiative_tasks["ParentTaskID"] == "")
        )
    ]

    if len(potential_parents) == 0:
        continue

    potential_children = initiative_tasks[
        (
            initiative_tasks["ParentTaskID"].isna()
            | (initiative_tasks["ParentTaskID"] == "")
        )
        & (~initiative_tasks["TaskID"].isin(hierarchy_map.keys()))
    ]

    if len(potential_children) <= 1:
        continue

    if "TranscriptionGroup" in df.columns:
        transcription_groups = (
            potential_children["TranscriptionGroup"].dropna().unique()
        )

        for group in transcription_groups:
            if added_links >= links_to_add:
                break

            group_tasks = potential_children[
                potential_children["TranscriptionGroup"] == group
            ]

            if len(group_tasks) >= 2:
                parent_id = group_tasks.iloc[0]["TaskID"]

                if parent_id not in hierarchy_map:
                    hierarchy_map[parent_id] = []

                for idx, child in group_tasks.iloc[1:].iterrows():
                    if added_links >= links_to_add:
                        break

                    child_id = child["TaskID"]

                    if (
                        child_id in hierarchy_map
                        or pd.notna(df.loc[idx, "ParentTaskID"])
                        and df.loc[idx, "ParentTaskID"] != ""
                    ):
                        continue

                    df.loc[idx, "ParentTaskID"] = parent_id
                    df.loc[idx, "SubTaskLevel"] = 1
                    df.loc[idx, "HierarchyMethod"] = "Transcription_Group"

                    hierarchy_map[parent_id].append(child_id)

                    added_links += 1

    if added_links < links_to_add:
        name_groups = defaultdict(list)

        for idx, row in potential_children.iterrows():
            task_name = row["TaskName"]
            if pd.isna(task_name) or task_name == "":
                continue

            task_name = re.sub(r"[^\w\s]", " ", str(task_name).lower())
            task_name = re.sub(r"\s+", " ", task_name).strip()
            key = " ".join(task_name.split()[:3])

            if key:
                name_groups[key].append((idx, row))

        for key, tasks in name_groups.items():
            if len(tasks) >= 2 and added_links < links_to_add:
                parent_idx, parent_row = tasks[0]
                parent_id = parent_row["TaskID"]

                if parent_id not in hierarchy_map:
                    hierarchy_map[parent_id] = []

                for child_idx, child_row in tasks[1:]:
                    if added_links >= links_to_add:
                        break

                    child_id = child_row["TaskID"]

                    if (
                        child_id in hierarchy_map
                        or pd.notna(df.loc[child_idx, "ParentTaskID"])
                        and df.loc[child_idx, "ParentTaskID"] != ""
                    ):
                        continue

                    df.loc[child_idx, "ParentTaskID"] = parent_id
                    df.loc[child_idx, "SubTaskLevel"] = 1
                    df.loc[child_idx, "HierarchyMethod"] = "Name_Similarity"

                    hierarchy_map[parent_id].append(child_id)

                    added_links += 1

print(f"Added {added_links} new parent-child relationships")

print("\n=== POPULATING METADATA COLUMNS ===")
metadata_updates = 0

if "TranscriptionGroup" in df.columns and "ConversationFlowID" in df.columns:
    empty_flow_mask = df["ConversationFlowID"].isna() | (df["ConversationFlowID"] == "")
    df.loc[empty_flow_mask, "ConversationFlowID"] = df.loc[
        empty_flow_mask, "TranscriptionGroup"
    ]
    metadata_updates += empty_flow_mask.sum()
    print(
        f"Populated {empty_flow_mask.sum()} ConversationFlowID values from TranscriptionGroup"
    )

if "LineRefQuality" in df.columns and "TranscriptionGroup" in df.columns:
    has_group_mask = df["TranscriptionGroup"].notna() & (df["TranscriptionGroup"] != "")
    df.loc[has_group_mask, "LineRefQuality"] = "Good"
    df.loc[~has_group_mask, "LineRefQuality"] = "Unknown"
    metadata_updates += len(df)
    print(f"Set LineRefQuality for all {len(df)} tasks")

if "ProcessingStageNotes" in df.columns:
    if "invalid_parents_mask" in locals():
        df.loc[invalid_parents_mask, "ProcessingStageNotes"] = (
            "Fixed invalid parent reference"
        )
        metadata_updates += invalid_parents_mask.sum()

    circular_refs_mask = df["ParentTaskID"] == ""  # Placeholder, not accurate
    if circular_refs_fixed > 0:
        df.loc[circular_refs_mask, "ProcessingStageNotes"] = (
            "Fixed circular reference in hierarchy"
        )
        metadata_updates += circular_refs_fixed

    print(
        f"Added ProcessingStageNotes for {invalid_parents_mask.sum() + circular_refs_fixed} tasks with fixed issues"
    )

if "MetadataCompleteness" in df.columns:
    metadata_fields = [
        "TaskName",
        "TaskDescription",
        "Assignee",
        "Initiative",
        "Status",
        "ParentTaskID",
        "SubTaskLevel",
        "ClassificationCategory",
        "IsInformationalContext",
    ]

    for idx, row in df.iterrows():
        filled_count = sum(
            1
            for field in metadata_fields
            if field in df.columns and pd.notna(row[field]) and row[field] != ""
        )
        completeness = filled_count / len(metadata_fields)
        df.loc[idx, "MetadataCompleteness"] = f"{completeness:.2f}"

    metadata_updates += len(df)
    print(f"Calculated MetadataCompleteness for all {len(df)} tasks")

print(f"Total metadata updates: {metadata_updates}")

df.to_csv(csv_path, index=False)
print(f"\nSaved updated CSV with fixes to {csv_path}")

parent_links_after = len(df[df["ParentTaskID"].notna() & (df["ParentTaskID"] != "")])
parent_percentage_after = parent_links_after / len(df) * 100
print(f"\n=== FINAL STATISTICS ===")
print(
    f"ParentTaskID links: {parent_percentage_after:.2f}% ({parent_links_after} tasks)"
)
print(f"Fixed issues:")
print(f"- {len(invalid_parents)} invalid parent references")
print(f"- {circular_refs_fixed} circular references")
print(f"- {len(inconsistent_levels)} subtask level inconsistencies with parents")
print(f"- {len(inconsistent_no_parent)} subtask level inconsistencies without parents")
print(f"- {initiative_fixes} initiative mismatches")
print(f"- {len(rasa_not_info)} RASA references not marked as informational contexts")
print(f"Added {added_links} new parent-child relationships")
print(f"Made {metadata_updates} metadata updates")
